def patch_audioread_compat() -> None:
    """Bridge qwen_omni_utils' FFmpegAudioFile to newer librosa/soundfile.

    The preview utility passes an audioread FFmpegAudioFile object directly to
    librosa.load.  Newer soundfile releases reject that object, so decode its
    PCM iterator explicitly while retaining Qwen's use_audio_in_video path.
    """
    import audioread  # type: ignore
    import librosa  # type: ignore
    import numpy as np  # type: ignore

    original = librosa.load
    ff_cls = getattr(getattr(audioread, "ffdec", None), "FFmpegAudioFile", None)
    if ff_cls is None or getattr(librosa.load, "_qwen_smoke_compat", False):
        return

    def compat_load(path, *args, **kwargs):
        if not isinstance(path, ff_cls):
            return original(path, *args, **kwargs)
        target_sr = kwargs.get("sr", args[0] if args else 22050)
        raw = b"".join(iter(path))
        channels = int(getattr(path, "channels", 1) or 1)
        src_sr = int(getattr(path, "samplerate", target_sr) or target_sr)
        y = np.frombuffer(raw, dtype="<i2").astype("float32") / 32768.0
        if channels > 1 and y.size >= channels:
            y = y[: (y.size // channels) * channels].reshape(-1, channels).mean(axis=1)
        if target_sr is not None and src_sr != int(target_sr) and y.size:
            try:
                y = librosa.resample(y, orig_sr=src_sr, target_sr=int(target_sr))
            except TypeError:
                y = librosa.resample(y, src_sr, int(target_sr))
            src_sr = int(target_sr)
        return y, src_sr

    compat_load._qwen_smoke_compat = True
    librosa.load = compat_load
