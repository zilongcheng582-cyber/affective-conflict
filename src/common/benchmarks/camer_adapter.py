"""CPU-only native CA-MER protocol adapter.

The adapter describes raw MER2023 media and annotation provenance.  It never
opens a video decoder and never imports Qwen or CUDA libraries.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Iterable, Mapping


CAMER_LABEL_SPACE = (
    "angry",
    "happy",
    "surprise",
    "fear",
    "sad",
    "worry",
    "neutral",
    "doubt",
    "contempt",
)

CAMER_CONDITION_TAGS = {
    ("audio", True): "CAMER_AUDIO_ALIGNED_AVT",
    ("video", True): "CAMER_VIDEO_ALIGNED_AVT",
    ("audio", False): "CAMER_AUDIO_ALIGNED_AV_DIAG",
    ("video", False): "CAMER_VIDEO_ALIGNED_AV_DIAG",
}

# These are exact spelling variants of the nine native classes, not semantic
# merges (for example curious is intentionally not mapped to doubt).
CANONICAL_VARIANTS = {
    "worry": "worry",
    "worried": "worry",
    "surprise": "surprise",
    "surprised": "surprise",
    "fear": "fear",
    "fearful": "fear",
    "doubt": "doubt",
    "doubtful": "doubt",
    "contempt": "contempt",
    "contemptuous": "contempt",
}

CURRENT_VIDEO_PROCESSING_LIMIT = {
    "fps": 1.0,
    "max_pixels": 360 * 420,
    "use_audio_in_video": True,
}

CA_MER_NATIVE_REASONING = "CA_MER_NATIVE_REASONING"
CA_MER_CONTROLLED_LABEL = "CA_MER_CONTROLLED_LABEL"
CA_MER_NATIVE_REPLICATION_TYPE = "PHENOMENON REPLICATION / MODEL EXTENSION"
CA_MER_NATIVE_TASK = "reason_v2"
CA_MER_NATIVE_REASONING_INSTRUCTION = (
    "Please analyze all the clues in the video and reason out the emotional label "
    "of the person in the video."
)
CA_MER_NATIVE_LABEL_SPACE = (
    "neutral",
    "angry",
    "happy",
    "sad",
    "worry",
    "surprise",
    "fear",
    "contempt",
    "doubt",
)
CA_MER_NATIVE_GENERATION = {
    "task": CA_MER_NATIVE_TASK,
    "max_new_tokens": 500,
    "do_sample": False,
    "num_beams": None,
    "temperature": None,
    "official_source": "eval_emotion_EMER.py and eval_configs/eval_emotion_CAMER.yaml",
    "qwen_transfer_note": "task-level free-form deterministic generation; model mechanics are Qwen-specific",
}


def canonicalize_label(raw_label: Any) -> str | None:
    raw = "" if raw_label is None else str(raw_label).strip().casefold()
    if not raw:
        return None
    return CANONICAL_VARIANTS.get(raw, raw)


def label_record(raw_label: Any) -> dict[str, str | None]:
    return {"raw_label": None if raw_label is None else str(raw_label), "canonical_label": canonicalize_label(raw_label)}


def load_annotations(path: str | Path) -> dict[str, dict[str, Any]]:
    """Load one official CA-MER JSON and index it by extension-free sample ID."""
    records = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(records, list):
        raise TypeError("CA-MER annotations must be a JSON list")
    indexed: dict[str, dict[str, Any]] = {}
    for row in records:
        sid = Path(str(row.get("file_name", ""))).stem
        if not sid:
            raise ValueError("CA-MER annotation row has no file_name")
        if sid in indexed:
            raise ValueError(f"duplicate CA-MER annotation sample: {sid}")
        indexed[sid] = dict(row)
        indexed[sid]["sample_id"] = sid
    return indexed


def index_media(root: str | Path) -> dict[str, list[Path]]:
    root = Path(root)
    index: dict[str, list[Path]] = {}
    for path in sorted(root.rglob("*")):
        if path.is_file() and path.suffix.casefold() in {".mp4", ".avi"}:
            index.setdefault(path.stem, []).append(path)
    return index


def _source_reversal(kind: str, row: Mapping[str, Any]) -> tuple[str, str, str, str]:
    kind = kind.lower()
    if kind == "audio":
        return (
            "audio",
            "video",
            canonicalize_label(row.get("audio_pseudo_label")),
            canonicalize_label(row.get("video_pseudo_label")),
        )
    if kind == "video":
        return (
            "video",
            "audio",
            canonicalize_label(row.get("video_pseudo_label")),
            canonicalize_label(row.get("audio_pseudo_label")),
        )
    raise ValueError(f"unsupported CA-MER alignment kind: {kind}")


def build_sample(
    row: Mapping[str, Any],
    *,
    kind: str,
    media_path: str | Path,
    include_subtitle: bool,
) -> dict[str, Any]:
    """Build an AVT or AV diagnostic record from one annotation row and clip."""
    sid = str(row.get("sample_id") or Path(str(row.get("file_name", ""))).stem).strip()
    if not sid:
        raise ValueError("CA-MER sample has no sample_id")
    path = Path(media_path)
    if path.stem != sid:
        raise AssertionError(f"media {path.name} does not match annotation sample {sid}")
    diagnostic_source, competing_source, diagnostic_label, competing_label = _source_reversal(kind, row)
    subtitle = str(row.get("subtitle") or "")
    if include_subtitle and not subtitle:
        raise ValueError(f"AVT sample {sid} has no official subtitle")
    condition = CAMER_CONDITION_TAGS[(kind.lower(), include_subtitle)]
    return {
        "dataset": "CA-MER/MER2023",
        "regime": condition,
        "sample_id": sid,
        "condition": condition,
        "benchmark_target": canonicalize_label(row.get("final_label")),
        "benchmark_target_raw": row.get("final_label"),
        "native_label_space": list(CAMER_LABEL_SPACE),
        "diagnostic_source": diagnostic_source,
        "diagnostic_label": diagnostic_label,
        "diagnostic_label_raw": row.get(f"{diagnostic_source}_pseudo_label"),
        "competing_source": competing_source,
        "competing_label": competing_label,
        "competing_label_raw": row.get(f"{competing_source}_pseudo_label"),
        "input_video_path": str(path),
        "input_audio_path": str(path),
        "input_text_source": "official_CA-MER_subtitle" if include_subtitle else None,
        "subtitle": subtitle if include_subtitle else None,
        "subtitle_present": bool(include_subtitle),
        "use_audio_in_video": True,
        "video_processor_params": dict(CURRENT_VIDEO_PROCESSING_LIMIT),
        "source_annotation_file": row.get("_source_json"),
    }


def assert_same_native_sample(avt: Mapping[str, Any], av: Mapping[str, Any]) -> None:
    """Hard assertion that AVT and AV diagnostic use the same clip and row."""
    for key in ("sample_id", "input_video_path", "input_audio_path"):
        if avt.get(key) != av.get(key):
            raise AssertionError(f"CA-MER native pair mismatch in {key}")
    if not avt.get("subtitle_present") or av.get("subtitle_present"):
        raise AssertionError("CA-MER pair must be AVT with subtitle and AV diagnostic without subtitle")


def assert_annotation_media_match(sample_id: str, media_path: str | Path, row: Mapping[str, Any]) -> None:
    if str(sample_id) != Path(str(row.get("file_name", ""))).stem:
        raise AssertionError("sample ID does not match its official annotation row")
    if Path(media_path).stem != str(sample_id):
        raise AssertionError("sample ID does not match raw media basename")


def arbitration_fields(sample: Mapping[str, Any], prediction_label: str | None) -> dict[str, Any]:
    pred = canonicalize_label(prediction_label)
    diagnostic = canonicalize_label(sample.get("diagnostic_label"))
    competing = canonicalize_label(sample.get("competing_label"))
    return {
        "follows_diagnostic": None if pred is None else pred == diagnostic,
        "follows_competing": None if pred is None or competing is None else pred == competing,
        "other_or_abstain": pred is None or (pred != diagnostic and (competing is None or pred != competing)),
    }


def build_native_reasoning_prompt(subtitle: Any) -> str:
    """Use the verified official reason_v2 wording with Qwen raw-media inputs."""
    text = "" if subtitle is None else str(subtitle).strip()
    if not text:
        raise ValueError("CA-MER native reasoning requires the official subtitle")
    character_line = f"The person in video says: {text}. "
    # The official feature loader wraps media with <video>/<feature> placeholders.
    # Qwen receives raw video/audio, so only the verified task wording and subtitle
    # are transferred; architecture-specific feature placeholders are not copied.
    return f"{character_line}[{CA_MER_NATIVE_TASK}] {CA_MER_NATIVE_REASONING_INSTRUCTION}"


def build_native_reasoning_input(
    row: Mapping[str, Any],
    *,
    media_path: str | Path,
    subset: str,
) -> dict[str, Any]:
    """Build a traceable CA_MER_NATIVE_REASONING A+V+T input without decoding media."""
    subset_key = str(subset).strip().lower().replace("-", "_")
    allowed_subsets = {"audio_aligned", "video_aligned", "consistent"}
    if subset_key not in allowed_subsets:
        raise ValueError(f"unsupported CA-MER subset: {subset}")
    annotation_id = Path(str(row.get("file_name", ""))).stem
    media = Path(media_path)
    if not annotation_id:
        raise AssertionError("CA-MER annotation sample_id is missing")
    if media.stem != annotation_id:
        raise AssertionError("CA-MER annotation and media sample IDs differ")
    subtitle = str(row.get("subtitle") or "").strip()
    if not subtitle:
        raise AssertionError("CA-MER native reasoning requires an official subtitle")
    target_raw = row.get("final_label")
    target = canonicalize_label(target_raw)
    if not target:
        raise AssertionError("CA-MER benchmark target is missing")
    annotation_source = str(row.get("_source_json") or "official_CA-MER_annotation")
    return {
        "protocol_id": CA_MER_NATIVE_REASONING,
        "replication_type": CA_MER_NATIVE_REPLICATION_TYPE,
        "task": CA_MER_NATIVE_TASK,
        "subset": subset_key,
        "annotation_sample_id": annotation_id,
        "media_sample_id": media.stem,
        "subtitle_source": annotation_source,
        "subtitle": subtitle,
        "video_asset": str(media),
        "audio_asset": str(media),
        "input_video_path": str(media),
        "input_audio_path": str(media),
        "benchmark_target_raw": target_raw,
        "benchmark_target": target,
        "raw_target_record": label_record(target_raw),
        "native_label_space": list(CA_MER_NATIVE_LABEL_SPACE),
        "prompt": build_native_reasoning_prompt(subtitle),
        "output_contract": {
            "type": "free_form_reasoning",
            "raw_response_field": "raw_reasoning",
            "direct_label_mode": False,
            "preserve_raw_response": True,
        },
        "generation": dict(CA_MER_NATIVE_GENERATION),
        "video_processing": dict(CURRENT_VIDEO_PROCESSING_LIMIT),
    }


def serialize_scoring_interface() -> dict[str, Any]:
    """Describe official OV scoring without calling its external judges."""
    return {
        "interface": "CA_MER_OPEN_VOCABULARY_SET_SCORING",
        "generated_response_field": "raw_reasoning",
        "emotion_extraction": {
            "judge_provider": "OpenAI",
            "model": "gpt-3.5-turbo-16k-0613",
            "system_prompt": "You are an emotion analysis expert.",
            "user_prompt_template": (
                "Please assume the role of an expert in the field of emotions. "
                "We provide clues that may be related to the emotions of the characters. "
                "Based on the provided clues, please identify the emotional states of the main characters. "
                "Please separate different emotional categories with commas and output only the clearly "
                "identifiable emotional categories in a list format. Do not output empty lists. "
                "Input: {text} Output:"
            ),
            "external_call_in_remediation": False,
        },
        "synonym_grouping": {
            "judge_provider": "OpenAI",
            "model": "gpt-3.5-turbo-16k-0613",
            "prompt_source": "emer_evaluation/utils/chatgpt_q.py:get_openset_synonym",
            "normalization": "group synonymous open-vocabulary terms then map each group to its first term",
            "external_call_in_remediation": False,
        },
        "metrics": ["set_level_accuracy", "set_level_recall"],
        "failure_handling": "record empty extraction or judge failure; do not silently convert to a closed label",
        "reproducibility_status": "EXTERNAL_JUDGE_REPRODUCIBILITY_LIMITATION",
    }


def serialize_native_reasoning_output(raw_response: Any) -> dict[str, Any]:
    """Serialize free-form native output without invoking extraction or a judge."""
    return {
        "raw_reasoning": "" if raw_response is None else str(raw_response),
        "parse_status": "RAW_FREE_FORM_UNJUDGED",
        "prediction_label": None,
        "canonical_label": None,
        "external_judge_called": False,
    }
