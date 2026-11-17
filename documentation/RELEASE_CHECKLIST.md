# v1.0.0-core release checklist

**Current state:** The RStudio V4 numerical gate passed locally on 2026-11-17. All 15 original staging paths now exist in GitHub, with code and aggregate numeric outputs verified against the local staging archive, allowing for documented portability and line-ending edits. No GitHub release tag or Zenodo archive exists.

## Verified in the RStudio log
- Exact candidate pairs: 43,218; bidirectionally unique exact pairs: 4,789.
- Main linked regression N = 4,167.
- Model A beta = -0.08087728; Model B beta = -0.04053629.
- Model F beta = -0.03561263, clustered HC1 SE = 0.008497094.
- Tract-held-out five-fold pooled RMSE: HMDA only 0.3177784; HMDA + SDAT 0.2290860.
- 11-column HMDA import correction: 120,115 rows, 99 columns, zero parsing issues, no changes to other columns.
- Local staging: eight aggregate CSV outputs, three R scripts, two documentation files; local README, .gitignore, release manifest.
- Local MD5 check: 15 pre-manifest files, zero changes at time checked.

## Before uploading local staging files
- [x] Inspect staged R scripts and aggregate CSVs for restricted filenames/identifying fields; final manual review remains recommended.
- [x] Run scripts from freshly downloaded GitHub main archive with original HMDA and SDAT inputs; numerical gate passed on 2026-11-17.
- [ ] Keep the original, external SDAT/HMDA microdata, exact crosswalk, parcel IDs, deed records, and individual audit notes OUT of Git.
- [x] Compare ZIP files to original 15-file manifest (15/15 MD5 match); reconcile GitHub file changes separately in `LOCAL_STAGE_FILE_INVENTORY.md`.
- [ ] Confirm correct license and citation preferences with repository owner; do not invent either.
- [ ] Document high-leverage HC3 warning and nonfinite intermediate SE diagnostic; the principal reported SEs are finite.
- [ ] Clearly separate **core** results from unbundled interval matching, subgroup, bootstrap and deed corroboration.

## Before publishing a GitHub tag and Zenodo version
- [x] Fetch all 15 original staging paths from GitHub and confirm three scripts, eight aggregate CSV outputs, and documentation exist.
- [x] Fresh GitHub archive rerun passed `V4_NUMERICAL_GATE_PASSED` on 2026-11-17.
- [ ] Investigate and document whether intermediate HC3 NaNs affect any reported inferential claims before tagging.
- [ ] Confirm Zenodo repository integration is enabled before creating a GitHub release.
- [ ] Release tag: `v1.0.0-core` only after these checks.
- [ ] Record Git commit SHA, Zenodo version DOI, release date, input source/version provenance and manuscript data/code statement.

**Research limitations:** A bidirectionally unique statistical HMDA/SDAT link is not a validated property identity. Estimated coefficients are descriptive. Predictive improvement is conditional on the selected linked sample.


## Fresh GitHub download reproduction — 2026-11-17

The owner downloaded the repository `main` branch ZIP from GitHub, extracted it to a separate local test directory, verified the three `R/` scripts existed, copied independently held source datasets into this **local, noncommitted** folder, and ran `R/HMDA_SDAT_Clean_Session_Release_Gate_V4.R` on R 4.5.2 (Windows 11). The saved console log ended in **`V4_NUMERICAL_GATE_PASSED`**.

- HMDA input: 120,115; SDAT input: 63,304
- Matching population: 62,305; exact candidate pairs: 43,218; unique exact statistical links: 4,789
- Primary regression N: 58,587; linked complete-case N: 4,167
- Model A beta: -0.08087728; B beta: -0.04053629; F beta: -0.03561263, F tract-clustered HC1 SE: 0.008497094
- 5-fold out-of-tract CV N: 4,167; HMDA-only RMSE: 0.3177784; HMDA+SDAT RMSE: 0.2290860; reduction: 27.91%

### Warnings emitted

1. `In meatHC(x, type = type, omega = omega): HC3 covariances are numerically unstable for hat values close to 1 (and undefined if exactly 1)`, affecting observations including 202, 263, 264, 579, 580, 853, 884, 939, 946, and 952.
2. `In sqrt(diag(se)): NaNs produced`.

These warnings originate in intermediate HC3 calculations. Core V4 numerical assertions passed and reported headline SEs were finite, but this by itself does **not** certify all intermediate inferential statistics or establish independence from leverage pathologies. The final paper should disclose the diagnostic and justify the reporting covariance estimator. Do not construe statistical record matches as verified individual identities.

The verified procedure is a **fresh GitHub archive execution with independently held inputs**; the repository remains not self-contained because raw data are intentionally excluded.
