# Maryland HMDA–SDAT: Extended-analysis replication supplement (proposed v4.0.3)

This package adds six Python analysis scripts and aggregate outputs to the earlier R-based verified core v4.0.1/v4.0.2 GitHub files. It does NOT independently reproduce the entire manuscript or establish true HMDA-to-property identities. The analyses were previously executed on held source datasets; this portable package has passed syntax and aggregate-file integrity checks only, not an independent clean-environment rerun.

## Execute

Set `HMDA_SDAT_DATA_DIR` to a folder containing the independently obtained source files and run individual scripts from that directory, for example:

```bash
export HMDA_SDAT_DATA_DIR=/path/to/private/research/data
python extended/R/06_transaction_subset_regressions.py
```

Some scripts still expect their specific aggregate-output directory names under the data directory and may require adjustment to output paths. The datasets are not included and are subject to their source-provider terms. Do not claim fully push-button replication without an independent end-to-end check.

### Original private data dependencies (do not upload these)
- `loan_purposes_1_state_MD(3).csv` — HMDA source subset
- `SDAT_2025_Market_Sales_With_Census_Tracts.csv` — SDAT source extract
- `Maryland_Property_Sales_2025.csv` — limited August–December sales extract
- `HMDA_SDAT_final_analysis_ids.csv` — research linkage IDs (sensitive)

### Scientific caveats
- Transaction-source account/date/price agreement is not an independent mortgage identity test.
- The additional property-sales records cover August–December 2025 only.
- Simulated mismatches are hypothetical, not observed false-match rates.
- Outcome-related selection and differing observational windows limit causal or general-population interpretation.
- Aggregate files originate from the prior analysis session and have not been independently rerun as part of this package preparation.

### Source and provenance
This extension was assembled 2026-11-18 from the locally archived sensitivity-analysis, transaction-audit, and regression-output packages. The original v4.0.1 core verification remains a distinct validation exercise.
