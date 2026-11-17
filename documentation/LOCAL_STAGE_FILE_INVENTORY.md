# Uploaded staging archive reconciliation — 2026-11-17

The user provided `HMDA_SDAT_GitHub_Release_v1.0.0-core.zip`, a local staging archive with **15 manifest-listed files** and `RELEASE_MANIFEST.csv`.

## Source archive integrity
Each of the 15 archive files was checked against the **MD5 checksum supplied by the local manifest**: **15/15 matched**. The archive contained exactly those 15 files plus the manifest, no extra files.

## GitHub upload verification
All **15 corresponding repository paths** were individually fetched from GitHub on the `main` branch: **15/15 exist**. This includes:
- 3 R scripts (`R/`)
- 8 aggregate CSV results (`results/`)
- 2 local-run documentation text files (`documentation/`)
- `README.md` and `.gitignore`

The original main analysis script is byte-identical to its archived version; its Git blob SHA is:
`25db4a907ff6897e76b4c375dfafe327806454a2`.

The tract-grouped CV script also matches its archived Git blob SHA:
`2983e8807055c8ba689b5425392e77e4c69ce034`.

**Intentional differences from the original local staging manifest:**
- `README.md` expanded to describe current GitHub contents and limitations.
- `.gitignore` expanded to protect against accidental inclusion of microdata/credentials.
- The V4 verification runner was adapted to locate the companion scripts in the repository's `R/` folder, replacing the flat-layout assumption. It requires a fresh-clone R run to revalidate that portability adjustment.
- Some committed text/CSV files use LF line endings rather than the local Windows CRLF form; the numerical CSV contents are otherwise transcribed without modifying values.

Therefore, the local `RELEASE_MANIFEST.csv` is **a record of the original staging ZIP, not a byte-level checksum manifest for the current GitHub commit**. GitHub Git blob hashes must be used for repository integrity.

## Reproducibility and release restrictions
The confirmed local V4 run produced 4,789 exact links, 4,167 linked regression records, Model F SE 0.008497094, and five-fold out-of-fold RMSEs 0.3177784 (HMDA only) and 0.2290860 (HMDA + SDAT).

**Still required before a versioned release:**
- Fresh-clone test of the updated `R/` script layout with properly prepared, separately obtained HMDA/SDAT inputs.
- Documentation or resolution of HC3 leverage-related warnings and intermediate nonfinite SEs.
- Confirmation that only the exact-linkage core results are covered; the interval/subgroup/bootstrap/manual deed components of the manuscript are **not** fully reproduced.
- Owner confirmation of licensing and Zenodo integration before GitHub release archiving.

**No GitHub release tag or Zenodo DOI has been created.** The repository is public.
