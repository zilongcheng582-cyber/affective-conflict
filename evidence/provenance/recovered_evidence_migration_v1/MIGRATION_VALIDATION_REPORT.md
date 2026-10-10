# Migration validation report

POST_HOC_EXPLORATORY. Main baseline: `544ca0efae158df369a7b25dd110dc4254f67a7d`. Reused commits: `8679809a184408423f346f3d24d22c7f652ff09a`, followed by verified V2 `566e41c8f32ccf8090bc1c2ba20e366913434054`. No main push, forced checkout of historical assets, GPU, or model fitting.

## Identity and source differences

135 candidate files missing from checked GitHub branches; 87 byte-identical files reused from existing Claude branch; 86 frozen input files already identical on main. Thus 222 scientific/evidence payload files added relative to main, with 16,372,203 payload bytes. Same-path differing-hash main assets: zero. These counts exclude newly authored migration documentation and validation code. 58 source artifacts are held or superseded, with explicit reasons; raw originals have no upload authorization inferred from the private repository.

All 177 entries in the final AutoDL science manifest independently rehashed: zero failures. Source manifest SHA256 `3cc3cc1e4ba594dd3e50ad9512378b64c6db7b9516c05b84a4dcbafc27874c0a`. Original manifests are preserved as historical manifests, not falsely presented as complete public-checkout manifests. Migration SHA256SUMS covers every new tracked file except itself. Transformations retain original hashes and all rows; no original sample, label or trial is altered.

## Actual CPU validation

`AUTODL_LOCAL_REPLAY_PASS`: an independent new-output invocation of frozen Phase4 replay yielded six exact SHA256 matches. It verified 6,354 corrected measurements, 9,219 frozen predictions and the fixed source bindings without refitting. Full historical extraction still uses restricted AutoDL inputs and reference backups.

Independent stdlib validation over public frozen prediction features re-evaluated all 18 route/baseline groups (legal M0, diagnostic source-only M0+ORDER, frozen M3a/M3b). Identities and evaluated denominators match; maximum metric absolute error `2.220446049250313e-16` <= 1e-12. CIs are preserved from their original frozen reports; this portable check does not regenerate bootstrap CIs or redefine populations. 5,199 strict recovered links and all six claim categories / 25 claims checked. MCR 4,000, CA-MER 6,000 and LISTEN 1,149 per-version safe projections parse and preserve planned failures; CA-MER scientific usable count is 5,825.

## Safety and limitations

Secret, private-key, personal-path, file-type and size checks: no findings in allowlisted content. Media, dataset archives, weights, environments, complete logs, credentials and unauthorized raw text remain excluded. New scientific payloads use scoped byte-preserving Git attributes. Existing main byte comparison passes; Windows checkout conversion was corrected only in the new migration clone, with no content changes to Git blobs.

Clean checkout: PENDING final isolated validation. The public repository supports independent audit and fixed metric replay; **GITHUB_CLEAN_CHECKOUT_FULLY_REPRODUCIBLE** is not claimed for complete raw-archive extraction or every exploratory bootstrap. Native and controlled MCR, V3/V4 LISTEN, seven-class B3 and sixteen-class CA-MER remain distinct. Earlier GPU proposals are preserved historical interpretations, not new experiment authorization.

Six CPU library modules imported successfully. Frozen closure and evidence-anchor tests: **36 passed**. Initial default Temp fixture setup was inaccessible; the successful rerun used an explicit workspace temp directory. Post-replay AutoDL source recheck again verified all177science entries, zero historical navigation changes and cleanERI1worktree.
