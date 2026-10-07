from __future__ import annotations

import re
import unicodedata
from typing import Any

PARSER_VERSION = "mcr_ser_parser_v1"
CANONICAL_LABELS = (
    "neutral",
    "happy",
    "surprised",
    "angry",
    "sad",
    "disgusted",
    "fearful",
)
_PATTERNS = {
    label: re.compile(r"(?<!\w)" + re.escape(label) + r"(?!\w)")
    for label in CANONICAL_LABELS
}


def _result(
    raw_response: Any,
    normalized_response: str | None,
    parse_status: str,
    parsed_label: str | None,
    matched_labels: list[str],
    match_counts: dict[str, int],
) -> dict[str, Any]:
    return {
        "parser_version": PARSER_VERSION,
        "parse_status": parse_status,
        "parsed_label": parsed_label,
        "matched_labels": matched_labels,
        "match_counts": match_counts,
        "normalized_response": normalized_response,
        "raw_response": raw_response,
    }


def _normalize_response(raw_response: str) -> str:
    return unicodedata.normalize("NFKC", raw_response).casefold().strip()


def parse_mcr_ser_response(raw_response: Any) -> dict[str, Any]:
    """Deterministically map free-form text to one canonical label or failure."""
    if raw_response is None or not isinstance(raw_response, str):
        return _result(raw_response, None, "PARSE_FAIL_MALFORMED", None, [], {})
    normalized_response = _normalize_response(raw_response)
    if not normalized_response:
        return _result(raw_response, normalized_response, "PARSE_FAIL_EMPTY", None, [], {})
    match_counts = {
        label: len(pattern.findall(normalized_response))
        for label, pattern in _PATTERNS.items()
        if pattern.search(normalized_response)
    }
    matched_labels = [label for label in CANONICAL_LABELS if label in match_counts]
    if len(matched_labels) == 0:
        return _result(raw_response, normalized_response, "PARSE_FAIL_NO_LABEL", None, [], {})
    if len(matched_labels) > 1:
        return _result(
            raw_response,
            normalized_response,
            "PARSE_FAIL_MULTIPLE_LABELS",
            None,
            matched_labels,
            match_counts,
        )
    label = matched_labels[0]
    return _result(raw_response, normalized_response, "PARSE_OK", label, matched_labels, match_counts)
