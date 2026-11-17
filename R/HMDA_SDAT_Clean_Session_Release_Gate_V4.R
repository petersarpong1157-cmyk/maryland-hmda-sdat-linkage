# Release gate V4: corrected 11-column HMDA import, income-log evaluation, same models & CV
# HMDA-SDAT clean-session reproducibility gate; SELECTIVE FIX for unseen categorical levels.
# Only change to main script: remove redundant out-of-model prediction, overwritten immediately.
# Run in a NEW RStudio session (Session > Restart R), not in a session with cached objects.
# Set project_dir below, then source this script.  It does NOT publish to GitHub or Zenodo.

project_dir <- Sys.getenv("HMDA_SDAT_PROJECT_DIR", unset = getwd())
# If your files are in another folder, change project_dir above.

stopifnot(dir.exists(project_dir))
required_packages <- c("readr", "dplyr", "tibble", "lmtest", "sandwich", "Matrix", "glmnet")
missing_packages <- required_packages[!vapply(required_packages, requireNamespace, logical(1), quietly=TRUE)]
if (length(missing_packages)) stop("Missing R packages. Install first: ", paste(missing_packages, collapse=", "))

main_script <- file.path(project_dir, "Paper1_QREF_Version2_Reproduction_IMPORT_FIXED.R")
cv_script <- file.path(project_dir, "HMDA_SDAT_Tract_Grouped_CV_and_Selection_PRINT_FIX.R")
sdat_source <- file.path(project_dir, "SDAT_2025_Market_Sales_With_Census_Tracts.csv")
hmda_source <- c(file.path(project_dir,"loan_purposes_1_state_MD.csv"),
                 file.path(project_dir,"loan_purposes_1_state_MD(3).csv"))
hmda_source <- hmda_source[file.exists(hmda_source)]
if (!length(hmda_source)) stop("HMDA input CSV not found in project_dir")
if (!file.exists(main_script) || !file.exists(cv_script) || !file.exists(sdat_source))
  stop("Required R script or SDAT CSV missing. Copy the supplied scripts to project_dir.")

# Use a unique run directory: no overwriting any existing analysis or public release files.
run_folder <- paste0("HMDA_SDAT_clean_run_",format(Sys.time(),"%Y%m%d_%H%M%S"))
run_dir <- file.path(project_dir, run_folder)
if (!dir.create(run_dir, recursive=TRUE, showWarnings=FALSE)) stop("Could not create run directory")
file.copy(hmda_source[1], file.path(run_dir,"loan_purposes_1_state_MD.csv"), overwrite=FALSE)
file.copy(sdat_source, file.path(run_dir,"SDAT_2025_Market_Sales_With_Census_Tracts.csv"), overwrite=FALSE)
original_main <- file.path(project_dir, "Paper1_QREF_Version2_Reproduction (1).R")
source_files <- c(main_script, cv_script, hmda_source[1], sdat_source, if (file.exists(original_main)) original_main)
write.csv(data.frame(file=basename(source_files), md5=unname(tools::md5sum(source_files))),
          file.path(run_dir,"source_md5.csv"),row.names=FALSE)
writeLines(c(paste("R version:",R.version.string), capture.output(sessionInfo())),
           file.path(run_dir,"session_info.txt"))
setwd(run_dir)

# Main script intentionally clears its global environment; use a local evaluation environment
# so this clean gate's run metadata is not deleted by the script's rm(list=ls()).
main_env <- new.env(parent=globalenv())
main_problem <- tryCatch({
  sys.source(main_script, envir=main_env)
  NULL
},error=function(e) conditionMessage(e))
if (!is.null(main_problem)) {
  writeLines(main_problem, file.path(run_dir,"FAILED_main_analysis.txt"))
  stop("Main analysis failed: ",main_problem)
}

# Compatibility alias: the source names the verified exact linkage table
# exact_bidirectional_pairs; the independent CV script calls it links.
if (!exists("links", envir=main_env, inherits=FALSE)) {
  if (!exists("exact_bidirectional_pairs", envir=main_env, inherits=FALSE))
    stop("Missing original exact_bidirectional_pairs after main analysis")
  main_env$links <- main_env$exact_bidirectional_pairs
}
if (nrow(main_env$links) != 4789L ||
    anyDuplicated(main_env$links$hmda_id) ||
    anyDuplicated(main_env$links$sdat_id))
  stop("Exact-link alias failed uniqueness or count checks")

required_main <- c("hmda_match_df","links","property_complete", "version2_results", "model_v2_tract")
if (!all(vapply(required_main,exists,logical(1),envir=main_env,inherits=FALSE))) {
  absent <- required_main[!vapply(required_main,exists,logical(1),envir=main_env,inherits=FALSE)]
  stop("Main run did not produce: ",paste(absent,collapse=", "))
}
if (nrow(main_env$hmda_match_df)!=62305L || nrow(main_env$links)!=4789L ||
    nrow(main_env$property_complete)!=4167L) stop("MAIN COUNTS FAILED; do not publish")

# Recalculate Model F robust SE directly from the new fitted model, retaining documented HC1.
se_F <- sqrt(diag(sandwich::vcovCL(main_env$model_v2_tract,
         cluster=~ census_tract,type="HC1")))["interest_rate_num"]
beta_F <- unname(coef(main_env$model_v2_tract)["interest_rate_num"])
write.csv(data.frame(model="F", beta=beta_F, HC1_tract_se=unname(se_F),
                     manuscript_SE=0.008497, prior_independent_output_SE=0.008506806132032736,
                     manuscript_gap=unname(se_F)-0.008497),
          file.path(run_dir,"clean_Model_F_check.csv"),row.names=FALSE)

# These are direct results from this run, NOT a comparison to an old CSV.
readr::write_csv(main_env$version2_results, file.path(run_dir,"clean_models_A_to_F.csv"))

# CV script relies on objects in the original main environment.
main_env$hmda_link <- main_env$hmda_match_df
main_env$hmda_path <- file.path(run_dir,"loan_purposes_1_state_MD.csv")
cv_problem <- tryCatch({sys.source(cv_script,envir=main_env);NULL},
                       error=function(e) conditionMessage(e))
if (!is.null(cv_problem)) {
  writeLines(cv_problem,file.path(run_dir,"FAILED_CV.txt"))
  stop("Grouped CV failed: ",cv_problem)
}
cv_out <- main_env$overall_results
readr::write_csv(cv_out,file.path(run_dir,"clean_cv_overall.csv"))

# Compare to TWO historical outputs without asserting equivalence of specifications.
find_rmse <- function(label) {
   row <- cv_out[as.character(cv_out$model)==label,,drop=FALSE]
   if (nrow(row)!=1L) stop("Expected one row for ",label)
   as.numeric(row$RMSE[1])
}
compare <- data.frame(
  model=c("HMDA_only","HMDA_plus_SDAT"),
  fresh_R_fixed_lambda_RMSE=c(find_rmse("HMDA_only"),find_rmse("HMDA_plus_SDAT")),
  manuscript_reported_RMSE=c(0.317778,0.229086),
  alternate_extended_output_RMSE=c(0.30333584522402496,0.21620079410702908)
)
compare$manuscript_gap <- compare$fresh_R_fixed_lambda_RMSE - compare$manuscript_reported_RMSE
compare$alternate_gap <- compare$fresh_R_fixed_lambda_RMSE - compare$alternate_extended_output_RMSE
readr::write_csv(compare,file.path(run_dir,"clean_prediction_provenance_comparison.csv"))

writeLines(c(
  "CLEAN RUN COMPLETED (results must still be inspected before publication)",
  paste("Output directory:",run_dir),
  paste("Model F HC1 tract-clustered SE:",format(se_F,digits=12)),
  "Check clean_models_A_to_F.csv, clean_Model_F_check.csv, clean_prediction_provenance_comparison.csv.",
  "Check methodological alignment of original CV folds/penalty before retaining manuscript figures.",
  "Do NOT publish manuscript, files, names, addresses or source deed images automatically."
),file.path(run_dir,"RUN_README.txt"))
cat("\nCLEAN RUN OUTPUT DIRECTORY:\n",run_dir,"\n")
print(compare)
cat("\nModel F SE:",se_F,"\n")

# V4 regression and CV release assertions: exact numbers derived from user's clean V3 rerun.
# Tight numerical tolerance is intentional; stop rather than publishing discrepant results.
check_close <- function(actual, expected, tolerance, what) {
  if (length(actual)!=1L || !is.finite(actual) || abs(actual-expected)>tolerance)
    stop(what, " differs: fresh=", actual, " expected=", expected,
         " tolerance=", tolerance, ". Do NOT release.")
}
lookup_beta <- function(label) {
  x <- main_env$version2_results
  idx <- which(grepl(label, x$model, fixed=TRUE))
  if(length(idx)!=1L) stop("Expected one model named ", label)
  as.numeric(x$interest_beta[idx])
}
check_close(lookup_beta("Model A - HMDA controls"), -0.08087728, 5e-7,"Model A beta")
check_close(lookup_beta("Model B - Property controls"), -0.04053629, 5e-7,"Model B beta")
check_close(beta_F, -0.03561263, 5e-7,"Model F beta")
check_close(se_F, 0.008497094, 5e-7,"Model F HC1 SE")
check_close(find_rmse("HMDA_only"), 0.3177784, 5e-6,"HMDA-only RMSE")
check_close(find_rmse("HMDA_plus_SDAT"), 0.2290860, 5e-6,"HMDA+SDAT RMSE")
writeLines(c("V4_NUMERICAL_GATE_PASSED", "11 HMDA categorical columns typed as character.",
             "See RUN_README.txt and warning audit; passage does not certify all inference."),
           file.path(run_dir,"V4_GATE_PASSED.txt"))
cat("\nV4_NUMERICAL_GATE_PASSED\n")
