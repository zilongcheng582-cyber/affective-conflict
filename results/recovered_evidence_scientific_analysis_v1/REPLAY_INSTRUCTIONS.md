# CPU replay

Historical source paths must be mounted unchanged. Python 3.12.3, numpy 2.3.2, scipy 1.18.1; no pandas, torch or model dependency is needed. Do not run historical model runners.

```bash
cd /root/autodl-tmp/affective-conflict-recovered-science-v1
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 python3 replay.py /root/autodl-tmp/affective-conflict-recovered-science-v1/replay_new > replay_new.log 2>&1
python3 -c 'import hashlib,pathlib; O=pathlib.Path("."); P=O/"replay_new"; names=[p for folder in ["numeric","intermediate"] for p in (P/folder).glob("*") if p.is_file()]; assert all(hashlib.sha256(p.read_bytes()).digest()==hashlib.sha256((O/p.relative_to(P)).read_bytes()).digest() for p in names); print("numeric replay PASS")'
```

Primary same-seed replay compared18numeric/tablefiles, all exactSHA matches. `diagnostics.py` fills the secondary predeclared source-label/distribution diagnostics; it was repeated in finalization with exacthash equality for its2new numerical files. Report-generation code is `finalize.py`; it reads existing numeric results and preserves frozen files. Its optional navigation maintenance is idempotent and documented; scientific recomputation itself only writes the nominated new output directory.

Plan families: sixMCRpairedsource-match contrasts(Holm); sixCApairedorder effects(Holm); threeLISTENdual-versus-nondual selection associations(Holm). Other intervals are pointwise exploratory/descriptive, not simultaneous tests. MCR943SHAbootstrap;CA/LISTENitem-level uncertainty with latent source dependence unverified. Seed20261010; bootstrap5000; cluster signflips19999.

After the authorized three navigation-only appends, `replay.py` maps exactly those references to saved byte-identical original docs. It verifies before/after hashes and never restores/rewrites the historical docs. All scientific inputs retain their original paths/hashes. The underlying statistical code, support sets and seeds are unchanged. `replay.py PATH --prepare-only` validated all original input bytes after this mapping; primary18/secondary2 numeric repeat checks remain valid.


## Mandatory Phase4 replay

Run `python3 /root/autodl-tmp/affective-conflict-recovered-science-v1/phase4_replay.py NEW_EMPTY_DIRECTORY`. It reads frozen release/archival assets, uses exact pre-append navigation backups, repeats fixed-coefficient prediction and descriptive subgroup calculations, then checks six deterministic outputs against SHA256. It never refits any model. Source locks and the navigation update records must remain present. Previous Phase1–3 replay remains valid with original byte-identical reference backups.
