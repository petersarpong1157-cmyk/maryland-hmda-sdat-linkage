# Maryland HMDA–SDAT Statistical Linkage Research

**Status: release candidate — core analysis only. No versioned release or DOI has been published from this repository.**

This repository is being prepared for a reproducibility release accompanying the study *Property Information, Record Linkage, and Specification Sensitivity in Mortgage Data: Evidence from Maryland HMDA and Assessment Records*.

## Scope
The verified core workflow analyzes 2025 Maryland HMDA and SDAT records, including exact tract/value statistical linkage, descriptive regression specifications A–F, selection diagnostics, and tract-grouped five-fold prediction.

**Important:** A unique statistical match is **not** a verified HMDA-to-property identity. Estimated rate–value relationships are conditional associations, not causal effects. Analyses use the selected statistically linked sample; predictive gains are not evidence of population-level predictive performance.

## Reference results (reproduced in the local V4 clean RStudio run on 2026-11-17)

| Check | Value |
| --- | ---: |
| Raw HMDA rows | 120,115 |
| Processed SDAT rows | 63,304 |
| HMDA matching population | 62,305 |
| Exact tract/value candidate pairs | 43,218 |
| Bidirectionally unique exact links | 4,789 |
| Primary complete-case regression observations | 58,587 |
| Exact-linked regression observations | 4,167 |
| Model A rate coefficient | -0.08087728 |
| Model B rate coefficient | -0.04053629 |
| Model F rate coefficient | -0.03561263 |
| Model F tract-clustered HC1 SE | 0.008497094 |
| HMDA-only pooled out-of-fold RMSE | 0.3177784 |
| HMDA + SDAT pooled out-of-fold RMSE | 0.2290860 |
| Relative pooled RMSE reduction | 27.91% |

Grouped CV uses five tract-held-out folds on N=4,167; these values pertain to the fixed-lambda R implementation, not alternative saved prediction outputs.

## Reproduction and inputs
The verified code was run in **R 4.5.2 on Windows 11**. Packages included readr, dplyr, tibble, lmtest, sandwich, Matrix, glmnet, and fixest. Source files must be independently obtained and prepared; public repository materials do **not** include HMDA/SDAT row-level inputs, individual linked records, deeds, or manual-audit details. The local V4 runner expects an input project directory set via `HMDA_SDAT_PROJECT_DIR` (default: current working directory).

The locally staged scripts and aggregate result CSVs have **not yet been copied into this repository**. Until they are, this README documents verified local results, **not** a runnable GitHub replication archive.

## Release coverage and outstanding validation
The core package does not independently reproduce all interval-linkage, subgroup, bootstrap, and manual corroboration analyses in the manuscript. HC3 leverage-related and nonfinite intermediate standard-error warnings appeared during the local run; the displayed rate coefficient SEs were finite, but a full coefficient-level diagnostics review remains appropriate. A prior import issue in 11 sparse HMDA categorical columns was fixed by explicit character types, and the corrected V4 gate reproduced the reference results.

## Provenance and citation
**Proposed tag:** `v1.0.0-core` (not yet created). Add a release DOI and citation metadata only after the verified repository version is archived with Zenodo. Do not cite this README as evidence that all manuscript analyses are reproducible from this repository alone.
