# ERI1 CPU reproducibility V1

Frozen ANALYSIS_RESULTS.json and OUTCOME_ACCOUNTING.csv replay byte-identically, including S1–S8, Holm adjustments, decisions and all sensitivities. Independent script rebuilds every cell from parsed labels and retains OTHER/PARSE_FAIL. All eight primary/S1 estimate, CI and p comparisons pass absolute tolerance 1e-12.

146 items × 16 cells = 2336 trials; no Pilot, retries or technical failures. Bootstrap: 10000 item resamples, primary seed 20261009, S1 seed 20261011. Sign-flip: 100000 two-sided draws, seeds 20261010 and 20261012. Independent implementation uses per-replicate resampling and different randomization batching; no frozen analysis functions are called.
