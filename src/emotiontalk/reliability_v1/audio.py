"""Frozen audio intervention specification (v1). Pure numpy/scipy; no model code.

Pipeline (identical for RECODE and every SNR condition, so SNRxx-vs-RECODE isolates the noise):
  1. Read the frozen source WAV (scipy.io.wavfile). Integer PCM -> float64 in [-1, 1) by dividing by 2**(bits-1);
     uint8 is centred at 128. Float WAV is taken as-is.
  2. Downmix to mono by the arithmetic mean over channels.
  3. Resample to 16,000 Hz with scipy.signal.resample_poly (exact rational up/down; Kaiser window, scipy default).
     Qwen2.5-Omni's loader also uses 16 kHz mono. Generating noise at 16 kHz makes the nominal SNR equal the
     SNR of the waveform the model's feature extractor receives (no later low-pass removes part of the noise).
  4. Signal power P_s = mean(x**2) over the whole 16 kHz clip (full-clip power; no VAD). P_s == 0 -> TECHNICAL failure.
  5. Noise: one base standard-normal realization z per item (numpy PCG64, seed = noise_seed(utterance_id)),
     length = len(x). For target SNR L dB: n = z * sqrt(P_s / (10**(L/10) * mean(z**2))). Realized SNR equals L
     up to floating-point error (checked to |error| <= 1e-6 dB). The same z is rescaled for 20/10/0 dB.
  6. y = x + n (RECODE: y = x). No normalization, no clipping. Written as 32-bit IEEE-float WAV, 16 kHz, mono.
     Peak |y| is recorded; values above 1.0 are retained (float WAV), not clipped.
  7. SHA256 of the written file is recorded and becomes the fail-closed identity used at inference time.
"""
import hashlib
import io
from math import gcd

import numpy as np
from scipy.io import wavfile
from scipy.signal import resample_poly

TARGET_SR = 16000
SPEC_VERSION = 'ERI1_AUDIO_SPEC_V1'


def to_float(data):
    if np.issubdtype(data.dtype, np.floating):
        x = data.astype(np.float64)
    elif data.dtype == np.uint8:
        x = (data.astype(np.float64) - 128.0) / 128.0
    elif np.issubdtype(data.dtype, np.integer):
        x = data.astype(np.float64) / float(2 ** (8 * data.dtype.itemsize - 1))
    else:
        raise ValueError('Unsupported WAV dtype ' + str(data.dtype))
    return x


def load_mono_16k(path_or_bytes):
    src = io.BytesIO(path_or_bytes) if isinstance(path_or_bytes, (bytes, bytearray)) else path_or_bytes
    sr, data = wavfile.read(src)
    x = to_float(data)
    channels = 1 if x.ndim == 1 else x.shape[1]
    if x.ndim == 2:
        x = x.mean(axis=1)
    if sr != TARGET_SR:
        g = gcd(int(sr), TARGET_SR)
        x = resample_poly(x, TARGET_SR // g, int(sr) // g)
    return x, {'source_sample_rate': int(sr), 'source_channels': int(channels), 'source_dtype': str(data.dtype),
               'source_frames': int(data.shape[0]), 'pipeline_frames_16k': int(len(x))}


def base_noise(seed, n):
    return np.random.default_rng(int(seed)).standard_normal(n)


def mix(x, z, snr_db):
    ps = float(np.mean(x ** 2))
    if not np.isfinite(ps) or ps <= 0:
        raise ValueError('TECHNICAL_ZERO_OR_NONFINITE_SIGNAL_POWER')
    if snr_db is None:
        return x.copy(), {'signal_power': ps, 'noise_power': 0.0, 'realized_snr_db': None}
    pz = float(np.mean(z ** 2))
    n = z * np.sqrt(ps / (10 ** (snr_db / 10.0) * pz))
    realized = 10 * np.log10(ps / float(np.mean(n ** 2)))
    if abs(realized - snr_db) > 1e-6:
        raise ValueError('REALIZED_SNR_OUT_OF_TOLERANCE')
    return x + n, {'signal_power': ps, 'noise_power': float(np.mean(n ** 2)), 'realized_snr_db': float(realized)}


def wav_bytes(y):
    buf = io.BytesIO()
    wavfile.write(buf, TARGET_SR, y.astype(np.float32))
    return buf.getvalue()


def make_variant(source_bytes, seed, snr_db):
    """Return (wav_bytes, metadata). snr_db None -> RECODE (same pipeline, no noise)."""
    x, meta = load_mono_16k(source_bytes)
    z = base_noise(seed, len(x))
    y, m2 = mix(x, z, snr_db)
    out = wav_bytes(y)
    # Re-read the written float32 file and recompute the stored-file SNR against the stored RECODE signal.
    _, back = wavfile.read(io.BytesIO(out))
    x32 = x.astype(np.float32).astype(np.float64)
    stored_snr = None
    if snr_db is not None:
        resid = back.astype(np.float64) - x32
        stored_snr = float(10 * np.log10(np.mean(x32 ** 2) / np.mean(resid ** 2)))
    meta.update(m2)
    meta.update({'spec_version': SPEC_VERSION, 'target_snr_db': snr_db, 'stored_file_snr_db': stored_snr,
                 'peak_abs': float(np.max(np.abs(back))), 'samples_above_unit': int(np.sum(np.abs(back) > 1.0)),
                 'output_sha256': hashlib.sha256(out).hexdigest(), 'output_sample_rate': TARGET_SR,
                 'output_format': 'WAV_IEEE_FLOAT32_MONO', 'noise_seed': int(seed)})
    return out, meta
