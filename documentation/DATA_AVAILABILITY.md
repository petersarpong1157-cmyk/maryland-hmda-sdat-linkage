# Data availability and safety

The repository is intended to provide reproducibility **code and aggregate results only**. It does not distribute the underlying HMDA loan-level dataset, Maryland SDAT transaction extract, unique record-linkage crosswalk, case-level predictions, personal addresses, deeds, or manual case review materials.

To reproduce the local analysis, a researcher must separately obtain the compatible 2025 Maryland HMDA and SDAT inputs, reconstruct the documented cohort, and supply the source files in the project directory expected by the R scripts. The local analysis used an HMDA table of 120,115 rows (99 columns) and an SDAT-derived 63,304-row table. These are **processed analysis inputs**, not standalone data included here.

Publicly released HMDA property values are coarsened; the interval sensitivity rule uses the half-open bin [HMDA midpoint minus $5,000, HMDA midpoint plus $5,000). Statistical linkage is not personal-identity confirmation.

Automated filename, header and keyword screens passed in the user’s local staging directory, but they are **not** a substitute for manual examination of all files and cell-level disclosure risks before publication.

The V4 clean-session core analysis was reproducible locally; additional manuscript interval/subgroup/bootstrap analyses are outside the proposed core release.
