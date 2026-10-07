# MCR Controlled Statistical Execution Addendum V2.1

This is a versioned statistical execution addendum only. It closes the numerical execution-parameter omission in the already-frozen dialogue-cluster bootstrap procedure. It does not alter populations, estimands, point estimates, parser behavior, prompt, manifest, or model outputs.

- Resampling unit: dialogue cluster
- Available dialogue clusters: 255
- Bootstrap replicates: B = 10000
- Confidence level: 95%
- Interval construction: ordinary percentile cluster-bootstrap interval; empirical 2.5th and 97.5th percentiles; NumPy linear percentile interpolation
- RNG: NumPy `Generator(PCG64)`
- Seed derivation: first 16 hexadecimal characters of frozen Analysis Spec V2 SHA256 `17230d00a0ce07305658b5de4cdeaf14cf830bd5c70e87a74bca6195ed6b04b7`, interpreted as an unsigned integer and reduced modulo `2**32`
- Derived seed: `2697856816`
- Duplicate cluster selections preserve multiplicity; all utterances, all four arms, and the paired `A_THEN_T` / `T_THEN_A` observations are retained.
- Dual-Readable uses the frozen observed indicator; readability is not recomputed inside replicates.
- No BCa, basic, studentized, or post-hoc hypothesis tests are calculated.

The addendum was created after V2 point estimates had been computed. It closes an execution-parameter omission in the pre-specified dialogue-cluster-bootstrap procedure; it does not alter populations, estimands, point estimates, or model outputs.
