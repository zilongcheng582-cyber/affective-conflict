"""CPU-only native MCR-Bench SER adapter.

No model or audio package is imported.  The adapter preserves the frozen text
fields and makes the paired audio invariant explicit.
"""

from __future__ import annotations

from typing import Any, Mapping, Sequence


MCR_CONDITIONS = ("neutral", "faithful", "adversarial", "irrelevant")
MCR_SER_LABELS = ("sad", "happy", "fearful", "angry", "surprised", "disgusted", "neutral")
PAPER_WARNING = (
    "The provided textual information may be accurate, inaccurate, or irrelevant. "
    "Use it with discretion when answering the question."
)


def _text(value: Any) -> str:
    return "" if value is None else str(value)


def _audio_key(row: Mapping[str, Any]) -> str:
    return _text(row.get("audio_sha256") or row.get("audio_path") or row.get("audio"))


def _question(row: Mapping[str, Any]) -> str:
    return _text(row.get("question") or row.get("question_text") or "What emotion is expressed in the audio?")


def build_condition(row: Mapping[str, Any], condition: str) -> dict[str, Any]:
    """Build one native MCR condition without rewriting its description."""
    condition = condition.lower()
    if condition not in MCR_CONDITIONS:
        raise ValueError(f"unsupported MCR condition: {condition}")
    audio_path = _text(row.get("audio_path") or row.get("audio"))
    if not audio_path:
        raise ValueError("MCR row has no audio asset")
    description = None if condition == "neutral" else _text(row.get(condition))
    if condition != "neutral" and description == "":
        raise ValueError(f"MCR row has no frozen {condition} text")
    prompt = _question(row) if condition == "neutral" else f"{description}\n{_question(row)}"
    return {
        "dataset": "MCR-Bench/SER",
        "sample_id": _text(row.get("sample_id") or row.get("original_record_index")),
        "condition": f"MCR_{condition.upper()}",
        "audio_path": audio_path,
        "audio_key": _audio_key(row),
        "description": description,
        "question": _question(row),
        "prompt": prompt,
        "benchmark_target": _text(row.get("gt")) or None,
        "native_label_space": list(MCR_SER_LABELS),
        "competitor_emotion": _text(row.get("competitor_emotion")) or None,
        "competitor_mapping_status": _text(row.get("competitor_mapping_status")) or None,
    }


def build_all_conditions(row: Mapping[str, Any]) -> list[dict[str, Any]]:
    return [build_condition(row, condition) for condition in MCR_CONDITIONS]


def assert_same_audio(conditions: Sequence[Mapping[str, Any]]) -> None:
    """Hard assertion for neutral/faithful/adversarial/irrelevant pairing."""
    if not conditions:
        raise AssertionError("empty MCR condition group")
    keys = {_audio_key(c) for c in conditions}
    if "" in keys or len(keys) != 1:
        raise AssertionError("MCR paired conditions do not share the exact audio asset")


def paired_transition(
    neutral_prediction: str | None,
    adversarial_prediction: str | None,
    benchmark_target: str | None,
) -> dict[str, Any]:
    """Return paired behavior fields; this does not calculate a scientific rate."""
    n = None if neutral_prediction is None else str(neutral_prediction)
    a = None if adversarial_prediction is None else str(adversarial_prediction)
    gt = None if benchmark_target is None else str(benchmark_target)
    n_correct = n is not None and gt is not None and n.casefold() == gt.casefold()
    a_correct = a is not None and gt is not None and a.casefold() == gt.casefold()
    return {
        "neutral_correct": n_correct,
        "adversarial_correct": a_correct,
        "correct_to_incorrect": bool(n_correct and not a_correct),
        "incorrect_to_correct": bool(not n_correct and a_correct),
        "prediction_changed": n != a,
        "prediction_unchanged": n == a,
    }


def assert_native_target(row: Mapping[str, Any]) -> None:
    target = _text(row.get("gt"))
    if not target or target not in MCR_SER_LABELS:
        raise AssertionError(f"MCR GT is not in the native seven-class SER space: {target!r}")
