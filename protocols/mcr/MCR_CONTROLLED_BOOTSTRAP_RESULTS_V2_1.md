# MCR Controlled Statistical Execution Addendum V2.1

This is a versioned statistical execution addendum only. It does not change V2 populations, estimands, point estimates, parser behavior, prompt, manifest, or model outputs.

## Frozen execution configuration

- Resampling unit: `dialogue_cluster`
- Dialogue clusters: `255`
- Replicates: `10000`
- Confidence level: `0.95`
- Interval: `ordinary percentile cluster-bootstrap; empirical 2.5th/97.5th percentiles; NumPy method=linear`
- RNG: `NumPy Generator(PCG64)`
- Derived seed: `2697856816`

## Reproducibility binding

- V2 point-estimate reproduction: `PASS`
- Source results SHA256: `009d2fadfe128ea2e7e512f972a112db8d7bd0949064bb6c7b12dc7315b874a6`
- Sample-level table SHA256: `e7c9f6ec9f65f87ba7f84a37275702e05c6695a9726cb045f846731046c21000`

## Dual-Readable primary 95% CIs

- Order-averaged `SIDE_AUDIO`: [0.089241, 0.135715]
- Order-averaged `SIDE_TEXT`: [0.854031, 0.902288]
- Order-averaged `OTHER`: [0.004123, 0.016234]
- Order-averaged `PARSE_FAIL`: [0.000000, 0.000000]
- ResolvedAudioShare: [0.090081, 0.136987]
- `A_THEN_T` `SIDE_AUDIO`: [0.029474, 0.067417]
- `A_THEN_T` `SIDE_TEXT`: [0.932583, 0.970526]
- `T_THEN_A` `SIDE_AUDIO`: [0.141593, 0.212330]
- `T_THEN_A` `SIDE_TEXT`: [0.766599, 0.841380]
- `STABLE_AUDIO`: [0.020576, 0.054670]
- `STABLE_TEXT`: [0.756705, 0.834025]
- `RECENCY_FLIP`: [0.108166, 0.172416]
- `PRIMACY_FLIP`: [0.002037, 0.017978]
- `OTHER_OR_INVALID`: [0.008247, 0.032468]
- `OS_RESOLVED`: [0.117778, 0.186297]

## Full-pool sensitivity CIs

- Order-averaged `SIDE_AUDIO`: [0.046841, 0.071931]
- Order-averaged `SIDE_TEXT`: [0.877900, 0.911509]
- Order-averaged `OTHER`: [0.035593, 0.057387]
- Order-averaged `PARSE_FAIL`: [0.000000, 0.000000]

No BCa, basic, studentized, or post-hoc hypothesis tests were calculated.

