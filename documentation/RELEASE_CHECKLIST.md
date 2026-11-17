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
- [ ] Confirm R scripts work from a fresh clone when the user supplies source inputs in the documented layout.
- [ ] Keep the original, external SDAT/HMDA microdata, exact crosswalk, parcel IDs, deed records, and individual audit notes OUT of Git.
- [x] Compare ZIP files to original 15-file manifest (15/15 MD5 match); reconcile GitHub file changes separately in `LOCAL_STAGE_FILE_INVENTORY.md`.
- [ ] Confirm correct license and citation preferences with repository owner; do not invent either.
- [ ] Document high-leverage HC3 warning and nonfinite intermediate SE diagnostic; the principal reported SEs are finite.
- [ ] Clearly separate **core** results from unbundled interval matching, subgroup, bootstrap and deed corroboration.

## Before publishing a GitHub tag and Zenodo version
- [x] Fetch all 15 original staging paths from GitHub and confirm three scripts, eight aggregate CSV outputs, and documentation exist.
- [ ] Re-run portable GitHub clone with prepared source inputs, document HC3 warnings, and freeze inspected commit; do not tag before this.
- [ ] Confirm Zenodo repository integration is enabled before creating a GitHub release.
- [ ] Release tag: `v1.0.0-core` only after these checks.
- [ ] Record Git commit SHA, Zenodo version DOI, release date, input source/version provenance and manuscript data/code statement.

**Research limitations:** A bidirectionally unique statistical HMDA/SDAT link is not a validated property identity. Estimated coefficients are descriptive. Predictive improvement is conditional on the selected linked sample.
