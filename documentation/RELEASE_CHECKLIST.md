# v1.0.0-core release checklist

**Current state:** The RStudio V4 numerical gate passed locally on 2026-11-17. This GitHub repository has not yet been certified as a faithful copy of the user’s local staging directory and has not been tagged or archived.

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
- [ ] Inspect actual staged source files and each CSV for individual identifying values and accidental microdata.
- [ ] Confirm R scripts work from a fresh clone when the user supplies source inputs in the documented layout.
- [ ] Keep the original, external SDAT/HMDA microdata, exact crosswalk, parcel IDs, deed records, and individual audit notes OUT of Git.
- [ ] Compare staged files to local `RELEASE_MANIFEST.csv`, regenerating it after any content edits.
- [ ] Confirm correct license and citation preferences with repository owner; do not invent either.
- [ ] Document high-leverage HC3 warning and nonfinite intermediate SE diagnostic; the principal reported SEs are finite.
- [ ] Clearly separate **core** results from unbundled interval matching, subgroup, bootstrap and deed corroboration.

## Before publishing a GitHub tag and Zenodo version
- [ ] Audit the actual GitHub file tree for the intended scripts, documentation and eight aggregate CSVs.
- [ ] Match a GitHub commit to the final inspected content; do not tag a partial staging state.
- [ ] Confirm Zenodo repository integration is enabled before creating a GitHub release.
- [ ] Release tag: `v1.0.0-core` only after these checks.
- [ ] Record Git commit SHA, Zenodo version DOI, release date, input source/version provenance and manuscript data/code statement.

**Research limitations:** A bidirectionally unique statistical HMDA/SDAT link is not a validated property identity. Estimated coefficients are descriptive. Predictive improvement is conditional on the selected linked sample.
