-- Advanced SQL analytics portfolio
-- Window functions, CTEs, and cohort-style analysis against the
-- synthetic consumer-lending portfolio built by setup_sqlite_db.py.
-- Tested against SQLite 3.45 (run_queries.py executes every query below
-- and prints the results).

-- ============================================================
-- Query 1: Month-over-month roll-rate matrix using LAG()
-- (SQL equivalent of the PROC SQL self-join in
--  01-sas-to-python-r-migration/delinquency_roll_rate_analysis)
-- ============================================================
WITH bucket_with_prior AS (
    SELECT
        account_id,
        snapshot_month,
        delinquency_bucket,
        LAG(delinquency_bucket) OVER (
            PARTITION BY account_id ORDER BY snapshot_month
        ) AS prior_bucket
    FROM account_month_snapshot
)
SELECT
    prior_bucket AS bucket_from,
    delinquency_bucket AS bucket_to,
    COUNT(*) AS n_accounts,
    ROUND(
        100.0 * COUNT(*) / SUM(COUNT(*)) OVER (PARTITION BY prior_bucket),
        1
    ) AS pct_of_from_bucket
FROM bucket_with_prior
WHERE prior_bucket IS NOT NULL
GROUP BY prior_bucket, delinquency_bucket
ORDER BY prior_bucket, delinquency_bucket;


-- ============================================================
-- Query 2: Top 5 highest-balance accounts per product type
-- (RANK() / PARTITION BY -- classic "top-N per group" pattern)
-- ============================================================
WITH latest_month AS (
    SELECT MAX(snapshot_month) AS m FROM account_month_snapshot
),
ranked AS (
    SELECT
        a.product_type,
        s.account_id,
        s.balance,
        RANK() OVER (
            PARTITION BY a.product_type ORDER BY s.balance DESC
        ) AS balance_rank
    FROM account_month_snapshot s
    JOIN accounts a ON a.account_id = s.account_id
    JOIN latest_month lm ON s.snapshot_month = lm.m
)
SELECT product_type, account_id, balance, balance_rank
FROM ranked
WHERE balance_rank <= 5
ORDER BY product_type, balance_rank;


-- ============================================================
-- Query 3: 3-month moving average of total portfolio balance per product
-- (AVG() OVER with a ROWS frame -- moving-average pattern used for
--  smoothing monthly financial/risk reporting)
-- ============================================================
WITH monthly_balance AS (
    SELECT
        a.product_type,
        s.snapshot_month,
        SUM(s.balance) AS total_balance
    FROM account_month_snapshot s
    JOIN accounts a ON a.account_id = s.account_id
    GROUP BY a.product_type, s.snapshot_month
)
SELECT
    product_type,
    snapshot_month,
    total_balance,
    ROUND(
        AVG(total_balance) OVER (
            PARTITION BY product_type
            ORDER BY snapshot_month
            ROWS BETWEEN 2 PRECEDING AND CURRENT ROW
        ), 2
    ) AS moving_avg_3mo
FROM monthly_balance
ORDER BY product_type, snapshot_month;


-- ============================================================
-- Query 4: Origination-year cohort delinquency rate
-- (cohort / vintage analysis -- common credit-risk reporting pattern)
-- ============================================================
WITH latest_month AS (
    SELECT MAX(snapshot_month) AS m FROM account_month_snapshot
)
SELECT
    strftime('%Y', a.origination_date) AS origination_year,
    COUNT(*) AS n_accounts,
    ROUND(
        100.0 * SUM(CASE WHEN s.delinquency_bucket != 'Current' THEN 1 ELSE 0 END) / COUNT(*),
        1
    ) AS pct_delinquent
FROM accounts a
JOIN account_month_snapshot s ON s.account_id = a.account_id
JOIN latest_month lm ON s.snapshot_month = lm.m
GROUP BY origination_year
ORDER BY origination_year;
