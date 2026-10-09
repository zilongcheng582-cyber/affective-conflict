# EmotionTalk reliability intervention v1 (ERI1)

This is a controlled audio-degradation experiment on EmotionTalk AV conflicts. It tests whether input reliability causally shifts Qwen2.5-Omni's arbitration.
It is separate from the exploratory R1–R3 analyses and does not change them.

| File | Content |
|---|---|
| `PROTOCOL_V1.md` | Design, population, audio specification, identity rules |
| `ANALYSIS_PLAN_V1.md` | Locked estimands, tests, missingness, falsification and decision rules |
| `PILOT_PLAN_V1.md` | Technical pilot and its science-blind pass criteria |
| `GPU_EXECUTION_PLAN_V1.md` | Environment, workload, memory, checkpoint/resume |
| `ELIGIBILITY_AND_SAMPLING_V1.csv` | All 1,500 panel items with eligibility, exclusion reasons, pilot flag |
| `FROZEN_TRIAL_MANIFEST_V1.csv` | 2,336 trials: ID, item, condition, arm/order, candidate sequence, noise seed, planned audio path, execution ranks |
| `PRE_EXECUTION_AMENDMENT_001.md` | Pre-execution amendment: directional missing-data bounds; S7 restricted to an exploratory conditional reference |
| `DESIGN_FREEZE_RECORD_V1.json` | SHA256 of design inputs, assets, protocol docs, code and tests |

Code: `src/emotiontalk/reliability_v1/` (`design`, `audio`, `bind_media`, `run`, `pilot_check`, `analyze`). Tests: `tests/test_reliability_v1.py`.

## 1. Fresh checkout, CPU verification (any machine)

```bash
git clone https://github.com/zilongcheng582-cyber/affective-conflict && cd affective-conflict
git checkout experiment/emotiontalk-reliability-intervention-v1     # design-freeze commit or later
python3.12 -m venv .venv && . .venv/bin/activate && pip install -r requirements.txt
python -m src.emotiontalk.reliability_v1.design --verify            # all checks true
python -m pytest -q                                                 # full suite incl. tests/test_reliability_v1.py
python -m src.emotiontalk.reliability_v1.run --phase full --output-dir /tmp/unused   # CPU_DRY_RUN_PASS, 2336 trials
python -m src.emotiontalk.reliability_v1.analyze --synthetic-dry-run --output-dir /tmp/eri1_synth   # pipeline check, SYNTHETIC
```

## 2. AutoDL: media binding (CPU; no GPU authorization needed)

```bash
export AF_WORK_ROOT=/root/autodl-tmp/affective-conflict AF_DATA_ROOT=/root/autodl-tmp/affective-conflict \
       AF_MODEL_DIR=/root/autodl-tmp/affective-conflict/models/Qwen2.5-Omni-7B
source /root/autodl-tmp/affective-conflict/envs/qwen25omni_recovered_v1/bin/activate   # frozen Python 3.12.3 env (has librosa)
cd /path/to/affective-conflict
python -m src.emotiontalk.reliability_v1.design --verify
python -m src.emotiontalk.reliability_v1.bind_media \
  --media-root /root/autodl-tmp/eri1_media_v1 \
  --binding-out /root/autodl-tmp/eri1_media_v1_binding/AUDIO_INTERVENTION_BINDING_V1.csv
sha256sum /root/autodl-tmp/eri1_media_v1_binding/AUDIO_INTERVENTION_BINDING_V1.csv
```

Copy the binding CSV to `experiments/emotiontalk_reliability_v1/AUDIO_INTERVENTION_BINDING_V1.csv`. Record its SHA256 in a short
`BINDING_RECORD_V1.json`, and commit both to the experiment branch **before** the pilot. Then validate every trial's media identity on CPU:

```bash
B=experiments/emotiontalk_reliability_v1/AUDIO_INTERVENTION_BINDING_V1.csv; H=$(sha256sum $B | cut -d' ' -f1)
python -m src.emotiontalk.reliability_v1.run --phase full --binding $B --binding-sha256 $H --output-dir /tmp/unused
# expect: CPU_DRY_RUN_PASS, binding_identity_check PASS_ALL_TRIAL_MEDIA_HASHES
```

## 3. AutoDL: technical pilot (needs separate GPU authorization)

```bash
OUT=/root/autodl-tmp/eri1_runs/pilot_v1
python -m src.emotiontalk.reliability_v1.run --phase pilot --binding $B --binding-sha256 $H --output-dir $OUT --execute-gpu --max-trials 10
python -m src.emotiontalk.reliability_v1.run --phase pilot --binding $B --binding-sha256 $H --output-dir $OUT --execute-gpu      # resume
python -m src.emotiontalk.reliability_v1.run --phase pilot --binding $B --binding-sha256 $H --output-dir $OUT --execute-gpu --retry-technical-failures
python -m src.emotiontalk.reliability_v1.pilot_check --pilot-dir $OUT --binding $B --binding-sha256 $H
```

## 4. Full run and analysis (only after pilot PASS and authorization)

```bash
FULL=/root/autodl-tmp/eri1_runs/full_v1
python -m src.emotiontalk.reliability_v1.run --phase full --binding $B --binding-sha256 $H --output-dir $FULL --execute-gpu   # repeat until done
python -m src.emotiontalk.reliability_v1.run --phase full --binding $B --binding-sha256 $H --output-dir $FULL --execute-gpu --retry-technical-failures
python -m src.emotiontalk.reliability_v1.analyze --trials $FULL/trials.jsonl --output-dir /root/autodl-tmp/eri1_runs/analysis_v1
```

Never reuse an output directory for a different phase, binding or code version. Never analyse pilot records.
