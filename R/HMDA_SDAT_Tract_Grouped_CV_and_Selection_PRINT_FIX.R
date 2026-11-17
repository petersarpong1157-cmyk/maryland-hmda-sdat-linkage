# HMDA-SDAT independent follow-on checks
# Run in SAME RStudio session after constructing hmda_link, links, and property_complete.
# No new causal or match-identity claims are supported by these checks.

suppressPackageStartupMessages({
  library(dplyr)
  library(readr)
  library(Matrix)
  library(glmnet)
})

stopifnot(exists('hmda_link'), exists('links'), exists('property_complete'))
stopifnot(nrow(hmda_link) == 62305L, nrow(links) == 4789L,
          nrow(property_complete) == 4167L)

out_dir <- dirname(hmda_path)
if (!dir.exists(out_dir)) out_dir <- getwd()

# ----------------------------------------------------------
# 1. Linkage selection by ORIGINAL HMDA property-value bands
# ----------------------------------------------------------
selected_ids <- unique(property_complete$hmda_id)
linked_ids <- unique(links$hmda_id)
selection_data <- hmda_link %>%
  mutate(
    link_status = case_when(
      hmda_id %in% selected_ids ~ 'final_regression',
      hmda_id %in% linked_ids ~ 'linked_excluded',
      TRUE ~ 'unlinked'
    ),
    income_num = suppressWarnings(as.numeric(income)),
    rate_num = suppressWarnings(as.numeric(interest_rate)),
    value_band = cut(
      property_value_num,
      breaks = c(-Inf,200000,350000,500000,750000,1000000,Inf),
      labels = c('<200k','200-350k','350-500k','500-750k','750k-1m','1m+'),
      right = FALSE
    )
  )

selection_summary <- selection_data %>%
  group_by(link_status) %>%
  summarise(n = n(),
            mean_property_value = mean(property_value_num, na.rm=TRUE),
            median_property_value = median(property_value_num, na.rm=TRUE),
            mean_interest_rate = mean(rate_num, na.rm=TRUE),
            mean_income_thousands = mean(income_num, na.rm=TRUE),
            .groups='drop')

value_bands <- selection_data %>%
  group_by(value_band) %>%
  summarise(
    total = n(),
    linked = sum(link_status != 'unlinked'),
    final_regression = sum(link_status == 'final_regression'),
    linkage_rate_pct = 100 * linked / total,
    regression_rate_pct = 100 * final_regression / total,
    .groups='drop'
  )

cat('\nSAMPLE SELECTION\n'); print(selection_summary, n=Inf)
cat('\nVALUE-BAND LINKAGE\n'); print(value_bands, n=Inf)
write_csv(selection_summary,file.path(out_dir,'verification_sample_selection.csv'))
write_csv(value_bands,file.path(out_dir,'verification_value_bands.csv'))

# ----------------------------------------------------------
# 2. Out-of-tract predictive check (not linkage verification)
# ----------------------------------------------------------
df <- property_complete
# Keep the exact manuscript outcome and predictor definitions.
stopifnot(all(c('log_property_value','interest_rate_num','log_income',
  'loan_term_num','dti_factor','occupancy_factor','construction_method_factor',
  'total_units_factor','county_factor','log_sqft','property_age',
  'grade_factor','dwelling_type_factor','census_tract') %in% names(df)))

needed <- c('log_property_value','interest_rate_num','log_income',
  'loan_term_num','dti_factor','occupancy_factor','construction_method_factor',
  'total_units_factor','county_factor','log_sqft','property_age',
  'grade_factor','dwelling_type_factor','census_tract')
stopifnot(all(complete.cases(df[,needed])), all(is.finite(df$log_property_value)))

# Use the same categorical levels and design columns in every fold.
# The categories are encoded without consulting the held-out outcomes.
baseline_formula <- ~ interest_rate_num + log_income + loan_term_num +
  dti_factor + occupancy_factor + construction_method_factor +
  total_units_factor + county_factor
augmented_formula <- ~ interest_rate_num + log_income + loan_term_num +
  dti_factor + occupancy_factor + construction_method_factor +
  total_units_factor + county_factor + log_sqft + property_age +
  grade_factor + dwelling_type_factor

xb <- Matrix::sparse.model.matrix(baseline_formula, data=df)[,-1,drop=FALSE]
xa <- Matrix::sparse.model.matrix(augmented_formula, data=df)[,-1,drop=FALSE]
y <- df$log_property_value
stopifnot(nrow(xb)==length(y), nrow(xa)==length(y),
          !anyNA(xb), !anyNA(xa))

# Deterministic, approximately balanced folds that never split a tract.
# Randomized tie order prevents systematic allocation by census-tract ID.
set.seed(20261116)
tract_count <- as.data.frame(table(as.character(df$census_tract)),
                             stringsAsFactors=FALSE)
names(tract_count) <- c('tract','n')
tract_count <- tract_count[sample.int(nrow(tract_count)), , drop=FALSE]
tract_count <- tract_count[order(-tract_count$n), , drop=FALSE]
loads <- integer(5)
tract_fold <- setNames(integer(nrow(tract_count)),tract_count$tract)
for (i in seq_len(nrow(tract_count))) {
  k <- which.min(loads)
  tract_fold[[tract_count$tract[i]]] <- k
  loads[k] <- loads[k] + tract_count$n[i]
}
fold_id <- unname(tract_fold[as.character(df$census_tract)])
stopifnot(!anyNA(fold_id), length(unique(fold_id))==5L)
cat('\nFOLD SIZES\n'); print(table(fold_id))

fit_and_score <- function(x,label,lambda=0.1) {
  oof <- rep(NA_real_,length(y))
  fold_result <- vector('list',5)
  for (k in 1:5) {
    train <- which(fold_id != k)
    test <- which(fold_id == k)
    fit <- glmnet::glmnet(x[train,,drop=FALSE], y[train],
                          family='gaussian', alpha=0, lambda=lambda,
                          standardize=TRUE, intercept=TRUE)
    pred <- as.numeric(predict(fit,newx=x[test,,drop=FALSE],s=lambda))
    oof[test] <- pred
    fold_result[[k]] <- data.frame(
      model=label, fold=k, test_n=length(test),
      RMSE=sqrt(mean((y[test]-pred)^2)),
      MAE=mean(abs(y[test]-pred)),
      R2=1-sum((y[test]-pred)^2)/sum((y[test]-mean(y[test]))^2)
    )
  }
  stopifnot(!anyNA(oof))
  list(folds=dplyr::bind_rows(fold_result),
       overall=data.frame(model=label,N=length(y),
             RMSE=sqrt(mean((y-oof)^2)),
             MAE=mean(abs(y-oof)),
             R2=1-sum((y-oof)^2)/sum((y-mean(y))^2)))
}

base <- fit_and_score(xb,'HMDA_only')
plus <- fit_and_score(xa,'HMDA_plus_SDAT')
fold_results <- dplyr::bind_rows(base$folds,plus$folds)
overall_results <- dplyr::bind_rows(base$overall,plus$overall)
cat('\nFIVE-FOLD RESULTS\n'); print(tibble::as_tibble(fold_results), n=Inf)
cat('\nOVERALL OUT-OF-FOLD RESULTS\n'); print(overall_results)
cat('Relative RMSE reduction (%):',
    round(100*(base$overall$RMSE-plus$overall$RMSE)/base$overall$RMSE,2),'\n')
write_csv(fold_results,file.path(out_dir,'verification_R_prediction_folds.csv'))
write_csv(overall_results,file.path(out_dir,'verification_R_prediction_overall.csv'))
cat('\nFiles saved to:',out_dir,'\n')
cat('NOTE: This is descriptive prediction WITHIN the statistically linked sample.\n')
cat('It cannot verify matched identities or establish causal mortgage-rate effects.\n')
