"""CPU-only native LISTEN protocol adapter.

This module deliberately contains no model, CUDA, datasets, or audio imports.  It
constructs the benchmark-native MCQ prompt and resolves a letter prediction after
inference has happened elsewhere.
"""

from __future__ import annotations

import hashlib
import json
import random
import re
from typing import Any, Iterable, Mapping, Sequence


LISTEN_CONDITIONS = {
    "3A": "LISTEN_MISMATCH_TEXT",
    "3B": "LISTEN_MISMATCH_AUDIO",
    "3C": "LISTEN_MISMATCH_AUDIO_TEXT",
}

OFFICIAL_AUGMENTED_EMOTIONS = (
    "neutral",
    "sadness",
    "surprise",
    "happiness",
    "fear",
    "anger",
    "excitement",
    "frustration",
)

MODALITY_INSTRUCTIONS = {
    "3A": "Read the transcription and classify the emotion.",
    "3B": "Listen to the audio and classify the emotion.",
    "3C": "Listen to the audio and read the transcription, then classify the emotion.",
}

# Named native mode for the Qwen2.5 model-level reproduction anchor.  This is
# metadata and a CPU-only protocol description; it never imports a model.
LISTEN_NATIVE_QWEN25 = "LISTEN_NATIVE_QWEN25"
LISTEN_NATIVE_REPLICATION_TYPE = "MODEL-LEVEL REPRODUCTION ANCHOR"

# The official LISTEN source uses explicit deterministic kwargs on the
# multimodal audio paths.  Text-only generation leaves those kwargs at the
# Transformers defaults; the distinction is retained instead of inventing one
# shared configuration.
LISTEN_NATIVE_GENERATION_BY_MODALITY = {
    "text_only": {
        "max_new_tokens": 3,
        "do_sample": None,
        "num_beams": None,
        "pad_token_id": None,
        "return_audio": False,
        "use_audio_in_video": False,
    },
    "audio_only": {
        "max_new_tokens": 3,
        "do_sample": False,
        "num_beams": 1,
        "pad_token_id": "tokenizer.eos_token_id",
        "return_audio": False,
        "use_audio_in_video": True,
    },
    "text_audio": {
        "max_new_tokens": 3,
        "do_sample": False,
        "num_beams": 1,
        "pad_token_id": "tokenizer.eos_token_id",
        "return_audio": False,
        "use_audio_in_video": True,
    },
}

LISTEN_NATIVE_MODEL_PROVENANCE = {
    "checkpoint": "Qwen/Qwen2.5-Omni-7B",
    "processor": "Qwen2_5OmniProcessor.from_pretrained",
    "model_loader": "Qwen2_5OmniForConditionalGeneration.from_pretrained",
    "torch_dtype": "torch.bfloat16",
    "device_map": "auto",
    "attn_implementation": "flash_attention_2",
    "chat_template": "processor.apply_chat_template(tokenize=False, add_generation_prompt=True)",
    "system_prompt": "You are Qwen, created by Alibaba Cloud. You are a helpful assistant.",
}


def _text(value: Any) -> str:
    return "" if value is None else str(value).strip()


def parse_choices(value: Any) -> list[str]:
    """Parse a native LISTEN choices field without changing its labels."""
    if value is None:
        return []
    if isinstance(value, str):
        raw = value.strip()
        if not raw:
            return []
        try:
            parsed = json.loads(raw)
        except json.JSONDecodeError:
            parsed = [x.strip() for x in raw.split("|") if x.strip()]
        value = parsed
    if isinstance(value, Mapping):
        value = list(value.values())
    if not isinstance(value, Iterable) or isinstance(value, (bytes, bytearray)):
        raise TypeError("choices must be a JSON/list-like value")
    return [_text(x) for x in value if _text(x)]


def choice_seed(global_seed: int, sample_id: str, condition: str) -> int:
    """Derive a stable per-sample seed; no process-global RNG is touched."""
    payload = f"{int(global_seed)}\x1f{sample_id}\x1f{condition}".encode("utf-8")
    return int.from_bytes(hashlib.sha256(payload).digest()[:8], "big")


def _unique(labels: Iterable[str]) -> list[str]:
    out: list[str] = []
    seen: set[str] = set()
    for label in labels:
        label = _text(label)
        key = label.casefold()
        if label and key not in seen:
            out.append(label)
            seen.add(key)
    return out


def ground_truth(row: Mapping[str, Any], condition: str) -> str:
    """Return the official mismatch GT for 3A/3B/3C."""
    condition = condition.upper()
    if condition == "3A":
        value = row.get("explicit_emotion") or row.get("answer_3A") or row.get("answer")
    elif condition in {"3B", "3C"}:
        value = row.get("implicit_emotion") or row.get("answer_3B") or row.get("answer")
    else:
        raise ValueError(f"unsupported LISTEN condition: {condition}")
    value = _text(value)
    if not value:
        raise ValueError(f"missing LISTEN ground truth for {condition}")
    return value


def build_prompt(
    row: Mapping[str, Any],
    condition: str,
    *,
    global_seed: int = 42,
    augment_emotions: bool = True,
) -> dict[str, Any]:
    """Construct the official-style prompt and its auditable choice mapping."""
    condition = condition.upper()
    if condition not in LISTEN_CONDITIONS:
        raise ValueError(f"unsupported LISTEN condition: {condition}")
    sample_id = _text(row.get("sample_id") or row.get("normalized_id"))
    if not sample_id:
        raise ValueError("LISTEN row requires sample_id or normalized_id")
    native_choices = parse_choices(row.get(f"choices_{condition}"))
    if not native_choices:
        native_choices = parse_choices(row.get("choices"))
    if not native_choices:
        raise ValueError("LISTEN row has no native choices")
    original_choices = _unique(native_choices)
    if augment_emotions and condition in {"3A", "3B", "3C"}:
        original_choices = _unique([*original_choices, *OFFICIAL_AUGMENTED_EMOTIONS])
    seed = choice_seed(global_seed, sample_id, condition)
    randomized = list(original_choices)
    random.Random(seed).shuffle(randomized)
    expected = ground_truth(row, condition)
    try:
        expected_position = next(i for i, x in enumerate(randomized) if x.casefold() == expected.casefold())
    except StopIteration as exc:
        raise ValueError(f"ground truth {expected!r} absent from choices") from exc
    expected_letter = chr(ord("A") + expected_position)
    question = _text(row.get(f"question_{condition}") or row.get("question"))
    transcription = _text(row.get("transcription"))
    lines = [MODALITY_INSTRUCTIONS[condition]]
    if condition in {"3A", "3C"}:
        lines.append(f"Transcription: {transcription}")
    if question:
        lines.append(question)
    lines.extend(f"{chr(ord('A') + i)}. {label}" for i, label in enumerate(randomized))
    lines.append(f"Respond with only the letter ({', '.join(chr(ord('A') + i) for i in range(len(randomized)))}):")
    return {
        "condition": LISTEN_CONDITIONS[condition],
        "condition_code": condition,
        "sample_id": sample_id,
        "original_choices": original_choices,
        "randomized_choices": randomized,
        "choice_seed": seed,
        "expected_letter": expected_letter,
        "expected_label": expected,
        "prompt": "\n".join(lines),
    }


def _candidate_letters(raw: str) -> list[str]:
    text = _text(raw)
    if not text:
        return []
    candidates: list[str] = []
    # Explicit answer/choice contexts, including “I choose A.”.
    context = re.compile(r"\b(?:answer|choice|option|letter|choose|select)\s*(?:is|:|=)?\s*\(?([A-Z])\)?\b", re.I)
    candidates.extend(m.upper() for m in context.findall(text) if m.upper() != "I")
    # A letter at the beginning of a line is an MCQ response or bullet.
    line_start = re.compile(r"^\s*\(?([A-Z])\)?(?=\s|[.:)\-]|$)", re.I | re.M)
    candidates.extend(m.upper() for m in line_start.findall(text) if m.upper() != "I")
    # Capture additional standalone alternatives (for example “A or B”) while
    # excluding the ordinary first-person pronoun from “I choose A”.
    standalone = re.findall(r"\b([A-Z])\b", text)
    candidates.extend(x.upper() for x in standalone if x.upper() != "I")
    return candidates


def parse_letter(raw: Any, randomized_choices: Sequence[str]) -> dict[str, Any]:
    """Resolve official-style letter output; conflicting letters are ambiguous."""
    text = _text(raw)
    candidates = _candidate_letters(text)
    unique = list(dict.fromkeys(candidates))
    allowed = {chr(ord("A") + i) for i in range(len(randomized_choices))}
    if not unique:
        status = "INVALID"
        letter = label = None
    elif len(unique) > 1:
        status = "AMBIGUOUS"
        letter = label = None
    elif unique[0] not in allowed:
        status = "INVALID"
        letter = label = None
    else:
        status = "PARSED"
        letter = unique[0]
        label = randomized_choices[ord(letter) - ord("A")]
    return {"prediction_letter": letter, "prediction_label": label, "parse_status": status}


def build_native_qwen25_record(
    row: Mapping[str, Any],
    condition: str,
    modality: str,
    *,
    global_seed: int = 42,
    augment_emotions: bool = True,
) -> dict[str, Any]:
    """Build an auditable LISTEN_NATIVE_QWEN25 pre-inference record."""
    modality_key = modality.casefold().replace("+", "_").replace("-", "_")
    aliases = {"text": "text_only", "audio": "audio_only", "audio_text": "text_audio", "text_audio": "text_audio"}
    modality_key = aliases.get(modality_key, modality_key)
    if modality_key not in LISTEN_NATIVE_GENERATION_BY_MODALITY:
        raise ValueError(f"unsupported LISTEN native modality: {modality}")
    record = build_prompt(row, condition, global_seed=global_seed, augment_emotions=augment_emotions)
    record.update(
        {
            "protocol_id": LISTEN_NATIVE_QWEN25,
            "replication_type": LISTEN_NATIVE_REPLICATION_TYPE,
            "modality": modality_key,
            "global_seed": int(global_seed),
            "choice_order": list(record["randomized_choices"]),
            "generation": dict(LISTEN_NATIVE_GENERATION_BY_MODALITY[modality_key]),
            "model_provenance": dict(LISTEN_NATIVE_MODEL_PROVENANCE),
        }
    )
    return record


def parse_native_qwen25_output(raw: Any, randomized_choices: Sequence[str]) -> dict[str, Any]:
    """Parse native output while rejecting ambiguity instead of guessing."""
    parsed = parse_letter(raw, randomized_choices)
    return {
        "parse_status": parsed["parse_status"],
        "prediction_letter": parsed["prediction_letter"],
        "prediction_label": parsed["prediction_label"],
    }


def arbitration_fields(
    condition: str,
    prediction_label: str | None,
    *,
    explicit_emotion: str | None,
    implicit_emotion: str | None,
) -> dict[str, Any]:
    """Map a native prediction into the post-prediction arbitration representation."""
    condition = condition.upper()
    pred = _text(prediction_label).casefold() or None
    explicit = _text(explicit_emotion).casefold() or None
    implicit = _text(implicit_emotion).casefold() or None
    if condition == "3A":
        return {
            "diagnostic_source": "text",
            "diagnostic_label": explicit,
            "competing_source": None,
            "competing_label": None,
            "follows_diagnostic": None,
            "follows_competing": None,
            "other_or_abstain": pred is not None and pred != explicit,
        }
    if condition not in {"3B", "3C"}:
        raise ValueError(f"unsupported LISTEN condition: {condition}")
    follows_diag = pred is not None and implicit is not None and pred == implicit
    follows_comp = pred is not None and explicit is not None and pred == explicit
    return {
        "diagnostic_source": "audio_implicit_affect",
        "diagnostic_label": implicit,
        "competing_source": "text_lexical_affect",
        "competing_label": explicit,
        "follows_diagnostic": follows_diag,
        "follows_competing": follows_comp,
        "other_or_abstain": pred is None or not (follows_diag or follows_comp),
    }


def assert_traceable(row: Mapping[str, Any], condition: str) -> None:
    """Ensure 3A/3B/3C retain the same underlying mismatch identity."""
    sid = _text(row.get("sample_id") or row.get("normalized_id"))
    if not sid:
        raise AssertionError("LISTEN sample identity is missing")
    if condition.upper() not in LISTEN_CONDITIONS:
        raise AssertionError(f"unknown LISTEN condition {condition}")
    if row.get("id_3A") and row.get("id_3B"):
        base = _text(row.get("normalized_id"))
        if base and not (_text(row["id_3A"]).startswith(base) and _text(row["id_3B"]).startswith(base)):
            raise AssertionError("3A/3B IDs do not trace to the same LISTEN sample")
