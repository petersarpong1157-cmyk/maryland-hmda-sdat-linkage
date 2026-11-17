# Local staging manifest — provenance only

On 2026-11-17 the researcher supplied the original local `RELEASE_MANIFEST.csv` plus the corresponding 243-byte `.gitignore` and 1,955-byte `README.md`. The two uploaded text files match the MD5 values recorded in the local manifest:

- `.gitignore`: `64dbd05331dadded9546f81c8daaf5d5`
- `README.md`: `1848e6bf99f31c88a4219741f8461bc0`

**This is NOT a checksum manifest of this GitHub commit.** GitHub's README and .gitignore have been expanded for safety and therefore will not have those MD5 hashes. The local manifest inventories **15** files, but only **three** of those files were attached in the latest upload. Do not claim GitHub has been validated against the entire manifest.

## Pending local files to transfer and validate

### R analysis scripts
- `R/HMDA_SDAT_Clean_Session_Release_Gate_V4.R` — original staged MD5 `ddd6b68ebe6262d63b99d05861ae99c0`; the local user corrected its hardcoded path, so any exported version must be compared carefully
- `R/HMDA_SDAT_Tract_Grouped_CV_and_Selection_PRINT_FIX.R` — `e5ab449d128d04174e2b18b25cb3e3b4`
- `R/Paper1_QREF_Version2_Reproduction_IMPORT_FIXED.R` — `24758f5073365d1012b3cd5f0e2a73e8`

### Aggregate CSV results
- `results/clean_cv_overall.csv` — `5fe33704f433e486bbe530e700ac0659`
- `results/clean_Model_F_check.csv` — `a563ab80ca26676c2a7a82b523d9cf8b`
- `results/clean_models_A_to_F.csv` — `4774513d8a0e4ee85339d209a6a8e21b`
- `results/clean_prediction_provenance_comparison.csv` — `2f3c7d521b5b29a6adc1ea535e74a793`
- `results/verification_R_prediction_folds.csv` — `daaee4061200fdfffe786c36d1efadd5`
- `results/verification_R_prediction_overall.csv` — `5fe33704f433e486bbe530e700ac0659`
- `results/verification_sample_selection.csv` — `5d3045ee8f8d2c2202a9d3fdb8b770e2`
- `results/verification_value_bands.csv` — `db3f4f5eceeb21f2806811bddfd27f57`

### Local documentation
- `documentation/RELEASE_REVIEW.txt` — `9eaa35db22fe5b0071dd27859b9c7e20`
- `documentation/session_info.txt` — `4799f9f379d0002a60d5c1f5a21bf2a9`

## Release gate

Do not create `v1.0.0-core` or archive to Zenodo until (a) the full staged payload is reviewed for microdata and private identifiers, (b) files are imported and verified at the final commit, and (c) outstanding HC3 diagnostics and the incomplete interval/subgroup/bootstrap coverage are documented. This inventory is a request for the missing content, not a public-data validation certificate.
