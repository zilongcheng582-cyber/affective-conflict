"""CURRENT_AUTHORITATIVE_IMPLEMENTATION: extracted frozen source scoring functions; no inference on import."""
import math
ONTOLOGY = ("angry", "disgusted", "fearful", "happy", "neutral", "sad", "surprised")

def normalize_template_result(value):
    if isinstance(value, str):
        return value, "str"
    if isinstance(value, list) and len(value) == 1 and isinstance(value[0], str):
        return value[0], "singleton_list_str"
    raise TypeError("chat template must return str or singleton list[str]")

def build_messages(sample, arm, prompt_config):
    instruction = prompt_config["instruction_template"].format(
        candidate_labels=", ".join(sample["candidate_labels"])
    )
    if arm == "T_ONLY":
        prompt_text = prompt_config["templates"][arm].format(
            instruction=instruction, text_evidence=sample["text"]
        )
        content = [{"type": "text", "text": prompt_text}]
        evidence_path = sample["text_json_path"]
    elif arm == "A_ONLY":
        prompt_text = prompt_config["templates"][arm].format(instruction=instruction)
        content = [{"type": "audio", "audio": sample["audio_path"]},
                   {"type": "text", "text": prompt_text}]
        evidence_path = sample["audio_path"]
    elif arm == "V_ONLY":
        prompt_text = prompt_config["templates"][arm].format(instruction=instruction)
        content = [{"type": "video", "video": sample["silent_video_path"]},
                   {"type": "text", "text": prompt_text}]
        evidence_path = sample["silent_video_path"]
    else:
        raise ValueError("unsupported gate arm")
    return [{"role": "user", "content": content}], prompt_text, evidence_path

def tokenizer_ids(tokenizer, text):
    encoded = tokenizer(text, add_special_tokens=False)
    ids = encoded["input_ids"]
    if ids and isinstance(ids[0], list):
        if len(ids) != 1:
            raise RuntimeError("tokenizer unexpectedly returned multiple rows")
        ids = ids[0]
    return [int(x) for x in ids]

def stable_softmax(values):
    peak = max(values)
    exps = [math.exp(x - peak) for x in values]
    total = sum(exps)
    return [x / total for x in exps]

def score_candidate_strings(rendered, inputs, sample, arm, processor, model, torch):
    """Score exact canonical continuations with the same thinker used by Omni generate()."""
    tokenizer = processor.tokenizer
    labels = list(sample["candidate_labels"])
    if len(labels) != 7 or len(set(labels)) != 7 or set(labels) != set(ONTOLOGY):
        raise RuntimeError("candidate labels do not equal the frozen seven-label ontology")
    prefix_ids = tokenizer_ids(tokenizer, rendered)
    actual_ids = [int(x) for x in inputs["input_ids"][0].detach().cpu().tolist()]
    suffix_n = min(16, len(prefix_ids), len(actual_ids))
    if suffix_n < 1 or prefix_ids[-suffix_n:] != actual_ids[-suffix_n:]:
        raise RuntimeError("assistant-generation prefix suffix tokenization differs from model input IDs")
    continuations = {}
    for label in labels:
        full_ids = tokenizer_ids(tokenizer, rendered + label)
        if full_ids[:len(prefix_ids)] != prefix_ids:
            raise RuntimeError(f"candidate boundary changes prefix tokenization: {label}")
        suffix = full_ids[len(prefix_ids):]
        if not suffix:
            raise RuntimeError(f"empty candidate continuation: {label}")
        continuations[label] = suffix

    base_inputs = dict(inputs)
    attention = base_inputs.get("attention_mask")
    if attention is None:
        attention = torch.ones_like(base_inputs["input_ids"], dtype=torch.long)
    prefix_len = int(attention[0].sum().item())
    if prefix_len < 1:
        raise RuntimeError("empty attention-masked prefix")
    base_ids = base_inputs["input_ids"][:, :prefix_len]
    base_attention = attention[:, :prefix_len]
    base_inputs["input_ids"] = base_ids
    base_inputs["attention_mask"] = base_attention
    with torch.inference_mode():
        base = model.thinker(**base_inputs, use_cache=False, use_audio_in_video=False)
        base_log_probs = torch.log_softmax(base.logits[0, prefix_len - 1].float(), dim=-1)
        del base
        score_rows = {}
        forward_calls = 1
        for label in labels:
            ids = continuations[label]
            if len(ids) == 1:
                token_logps = [float(base_log_probs[ids[0]].item())]
            else:
                suffix_tensor = torch.tensor([ids], dtype=base_ids.dtype, device=base_ids.device)
                candidate_inputs = dict(base_inputs)
                candidate_inputs["input_ids"] = torch.cat([base_ids, suffix_tensor], dim=1)
                candidate_inputs["attention_mask"] = torch.cat([
                    base_attention,
                    torch.ones((1, len(ids)), dtype=base_attention.dtype, device=base_attention.device)
                ], dim=1)
                candidate_out = model.thinker(**candidate_inputs, use_cache=False,
                                              use_audio_in_video=False)
                forward_calls += 1
                token_logps = []
                for idx, token_id in enumerate(ids):
                    pred_pos = prefix_len - 1 + idx
                    token_log_probs = torch.log_softmax(candidate_out.logits[0, pred_pos].float(), dim=-1)
                    token_logps.append(float(token_log_probs[token_id].item()))
                    del token_log_probs
                del candidate_out, candidate_inputs, suffix_tensor
            raw_score = float(sum(token_logps))
            mean_score = raw_score / len(token_logps)
            score_rows[label] = {
                "token_ids": ids,
                "token_count": len(ids),
                "token_log_probabilities": token_logps,
                "sum_log_probability": raw_score,
                "mean_token_log_probability": mean_score,
            }
        del base_log_probs
    raw_scores = [score_rows[label]["sum_log_probability"] for label in labels]
    mean_scores = [score_rows[label]["mean_token_log_probability"] for label in labels]
    probs_raw = stable_softmax(raw_scores)
    probs_mean = stable_softmax(mean_scores)
    for i, label in enumerate(labels):
        score_rows[label]["probability_sum_score_sensitivity"] = probs_raw[i]
        score_rows[label]["probability_mean_score_primary"] = probs_mean[i]

    def entropy(p):
        h = -sum(x * math.log(x) for x in p if x > 0)
        return {"nats": h, "normalized_by_log7": h / math.log(7)}

    order = sorted(range(7), key=lambda i: (-probs_mean[i], i))
    top1, top2 = order[:2]
    raw_order = sorted(range(7), key=lambda i: (-probs_raw[i], i))
    source_field = {"T_ONLY": "text_emotion", "A_ONLY": "audio_emotion", "V_ONLY": "video_emotion"}[arm]
    source_label = sample[source_field]
    if source_label not in labels:
        raise RuntimeError(f"source-side label outside candidate ontology: {source_label}")
    source_idx = labels.index(source_label)
    return {
        "candidate_scoring_status": "OK",
        "candidate_scoring_method": "thinker_teacher_forced_exact_sequence_sum_and_mean_log_probability",
        "candidate_scoring_prefix_token_count": len(prefix_ids),
        "candidate_scoring_forward_calls": forward_calls,
        "candidate_token_counts": {label: len(continuations[label]) for label in labels},
        "candidate_scores": score_rows,
        "candidate_probability_method_primary": "softmax(mean_token_log_probability)",
        "candidate_probability_method_sensitivity": "softmax(sum_log_probability)",
        "candidate_score_argmax_primary": labels[top1],
        "candidate_score_argmax_sum_sensitivity": labels[raw_order[0]],
        "candidate_top1_primary": labels[top1],
        "candidate_top1_probability_primary": probs_mean[top1],
        "candidate_top2_primary": labels[top2],
        "candidate_top2_probability_primary": probs_mean[top2],
        "candidate_top1_top2_margin_primary": probs_mean[top1] - probs_mean[top2],
        "candidate_entropy_primary": entropy(probs_mean),
        "candidate_entropy_sum_sensitivity": entropy(probs_raw),
        "source_label_for_measurement_only": source_label,
        "source_label_probability_primary": probs_mean[source_idx],
        "source_label_probability_sum_sensitivity": probs_raw[source_idx],
        "score_greedy_parser_agreement": None,
    }
