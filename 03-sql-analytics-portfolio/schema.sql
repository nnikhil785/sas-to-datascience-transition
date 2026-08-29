-- Schema for the SQL analytics portfolio.
-- Models a simplified consumer-lending portfolio: accounts + monthly
-- account-level snapshots (balance, delinquency bucket) -- the same
-- shape of data behind the roll-rate / portfolio-reporting work
-- referenced throughout the resume.

DROP TABLE IF EXISTS accounts;
CREATE TABLE accounts (
    account_id      TEXT PRIMARY KEY,
    product_type    TEXT NOT NULL,       -- Credit Card, Auto Loan, Mortgage, Student Loan
    origination_date TEXT NOT NULL,
    credit_limit    REAL
);

DROP TABLE IF EXISTS account_month_snapshot;
CREATE TABLE account_month_snapshot (
    account_id          TEXT NOT NULL,
    snapshot_month      TEXT NOT NULL,   -- 'YYYY-MM'
    balance             REAL NOT NULL,
    delinquency_bucket  TEXT NOT NULL,   -- Current, 30DPD, 60DPD, 90DPD, ChargeOff
    FOREIGN KEY (account_id) REFERENCES accounts(account_id)
);

CREATE INDEX idx_snapshot_account_month ON account_month_snapshot(account_id, snapshot_month);
