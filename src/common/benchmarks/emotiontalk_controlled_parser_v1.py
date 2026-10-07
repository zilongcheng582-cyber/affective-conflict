"""Strict parser for frozen EmotionTalk candidate-label outputs."""

ONTOLOGY = (
    "angry",
    "disgusted",
    "fearful",
    "happy",
    "neutral",
    "sad",
    "surprised",
)


def parse_label(raw_text):
    """Accept only one ontology label after outer-whitespace removal.

    Matching is case-insensitive and returns the canonical lowercase source
    string. Any prose, punctuation, unknown value, or multiple-label response
    is a parse failure.
    """
    if not isinstance(raw_text, str):
        return {
            "parsed_label": None,
            "parser_status": "PARSE_FAIL",
            "raw_text": raw_text,
        }
    normalized = raw_text.strip().casefold()
    matches = [label for label in ONTOLOGY if normalized == label.casefold()]
    if len(matches) == 1:
        return {
            "parsed_label": matches[0],
            "parser_status": "OK",
            "raw_text": raw_text,
        }
    return {
        "parsed_label": None,
        "parser_status": "PARSE_FAIL",
        "raw_text": raw_text,
    }
