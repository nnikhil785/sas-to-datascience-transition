# Roll-Rate Analysis - R (base R) migration of roll_rate_analysis.sas
#
# Same business logic as the SAS version:
#   1. Load account-month delinquency data.
#   2. Self-join each account's bucket in month N to month N+1.
#   3. Build a bucket_from x bucket_to transition (roll-rate) matrix.
#   4. Convert counts to row-percentages.
#   5. Print a report-style summary.
#
# Deliberately written in base R (no tidyverse dependency) so it runs
# anywhere R is installed -- mirrors the SAS EG / R Studio statistical
# work referenced on the resume (Global Atlantic role).
#
# Run:
#   Rscript roll_rate_analysis.R

BUCKET_ORDER <- c("Current", "30DPD", "60DPD", "90DPD", "ChargeOff")

# Resolve path relative to this script regardless of working directory
this_file <- commandArgs(trailingOnly = FALSE)
script_path <- sub("--file=", "", this_file[grep("--file=", this_file)])
script_dir <- dirname(normalizePath(script_path))
data_path <- file.path(dirname(script_dir), "data", "account_month_delinquency.csv")

df <- read.csv(data_path, stringsAsFactors = FALSE)
df$delinquency_bucket <- factor(df$delinquency_bucket, levels = BUCKET_ORDER, ordered = TRUE)

# --- Step 2: self-join bucket at month N to bucket at month N+1 -------------
left <- df
names(left)[names(left) == "month"] <- "month_from"
names(left)[names(left) == "delinquency_bucket"] <- "bucket_from"

right <- df
right$month_from <- right$month - 1
names(right)[names(right) == "delinquency_bucket"] <- "bucket_to"

pairs <- merge(
  left[, c("account_id", "month_from", "bucket_from")],
  right[, c("account_id", "month_from", "bucket_to")],
  by = c("account_id", "month_from")
)

# --- Steps 3-4: transition matrix (counts -> row percentages) --------------
counts <- table(
  factor(pairs$bucket_from, levels = BUCKET_ORDER),
  factor(pairs$bucket_to, levels = BUCKET_ORDER)
)

row_pct <- prop.table(counts, margin = 1) * 100

cat("Roll-Rate Matrix - Account Counts (rows = From, cols = To)\n")
print(counts)
cat("\nRoll-Rate Matrix - Row Percentages\n")
print(round(row_pct, 1))

current_to_worse <- sum(row_pct["Current", c("30DPD", "60DPD", "90DPD", "ChargeOff")])
cat(sprintf("\nCurrent -> Any Delinquency roll rate: %.2f%%\n", current_to_worse))
