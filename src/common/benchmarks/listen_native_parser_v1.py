from __future__ import annotations

import re
from typing import Any, Sequence


def parse_listen_response(raw: Any, choices: Sequence[str]) -> dict[str, Any]:
    """Strict parser: exactly one A-J letter, optionally followed by . or )."""
    value = "" if raw is None else str(raw).strip()
    n = len(choices)
    if n < 1 or n > 10:
        return {"status": "invalid_choice_count", "letter": None, "label": None, "raw": value}
    match = re.fullmatch(r"([A-Ja-j])(?:[.)])?", value)
    if not match:
        return {"status": "unparsed", "letter": None, "label": None, "raw": value}
    letter = match.group(1).upper()
    index = ord(letter) - ord("A")
    if index >= n:
        return {"status": "out_of_range", "letter": letter, "label": None, "raw": value}
    return {"status": "parsed", "letter": letter, "label": str(choices[index]), "raw": value}


def score_listen_response(raw: Any, choices: Sequence[str], target_label: str) -> dict[str, Any]:
    parsed = parse_listen_response(raw, choices)
    parsed["target_label"] = target_label
    parsed["correct"] = parsed.get("status") == "parsed" and parsed.get("label") == target_label
    return parsed
