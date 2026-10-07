"""Strict parser and outcome mapping for the CA-MER controlled arbitration protocol."""
from __future__ import annotations

import json
import string
from typing import Any, Iterable

OUTCOMES = ("SIDE_AUDIO", "SIDE_VIDEO", "OTHER", "PARSE_FAIL")
ARMS = ("A_ONLY", "V_ONLY", "A_THEN_V", "V_THEN_A")


def normalize_label(value: str) -> str:
    """Mechanical normalization only; never merges semantically related labels."""
    return str(value).casefold().strip().strip(
        string.whitespace + string.punctuation + "����"
    )


def parse_label(raw_text: str, candidates: Iterable[str]) -> tuple[str | None, str]:
    """Return (canonical candidate or None, status). Accept only a one-key JSON object."""
    try:
        obj: Any = json.loads(raw_text.strip())
    except (TypeError, json.JSONDecodeError):
        return None, "PARSE_FAIL"
    if not isinstance(obj, dict) or set(obj) != {"label"} or not isinstance(obj["label"], str):
        return None, "PARSE_FAIL"
    wanted = normalize_label(obj["label"])
    matches = [candidate for candidate in candidates if normalize_label(candidate) == wanted]
    if len(matches) != 1:
        return None, "PARSE_FAIL"
    return matches[0], "OK"


def conflict_outcome(predicted: str | None, y_audio: str, y_video: str) -> str:
    """Map a valid prediction to the source evidence side; other/invalid stays distinct."""
    if predicted is None:
        return "PARSE_FAIL"
    a, v, p = map(normalize_label, (y_audio, y_video, predicted))
    if a == v:
        return "OTHER"
    if p == a:
        return "SIDE_AUDIO"
    if p == v:
        return "SIDE_VIDEO"
    return "OTHER"


def consistent_control_outcome(predicted: str | None, y_consistent: str) -> str:
    """Score a consistent control separately from conflict-side outcomes."""
    if predicted is None:
        return "PARSE_FAIL"
    if normalize_label(predicted) == normalize_label(y_consistent):
        return "CONTROL_MATCH"
    return "CONTROL_OTHER"


def order_sensitivity(a_then_v: str, v_then_a: str) -> str:
    """Classify the joint-arm pair; recency/primacy labels describe order association only."""
    if a_then_v == v_then_a == "SIDE_AUDIO":
        return "STABLE_AUDIO"
    if a_then_v == v_then_a == "SIDE_VIDEO":
        return "STABLE_VIDEO"
    if a_then_v == "SIDE_VIDEO" and v_then_a == "SIDE_AUDIO":
        return "RECENCY_LIKE_FLIP"
    if a_then_v == "SIDE_AUDIO" and v_then_a == "SIDE_VIDEO":
        return "PRIMACY_LIKE_FLIP"
    return "OTHER_OR_INVALID"
