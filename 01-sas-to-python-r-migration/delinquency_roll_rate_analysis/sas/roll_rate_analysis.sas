/*-----------------------------------------------------------------------
  Roll-Rate Analysis - SAS (Base SAS / PROC SQL)
  ---------------------------------------------------------------------
  Purpose : Build a month-over-month delinquency-bucket transition
            ("roll-rate") matrix for a consumer credit portfolio.
            This is the classic PROC SQL + DATA step pattern used for
            monthly risk/portfolio reporting (see roll-rate bullets in
            resume: 30/60/90 DPD tracking, charge-off risk monitoring).

  Input   : account_month_delinquency (account_id, month, bucket, balance)
  Output  : roll_rate_matrix - counts and % of accounts transitioning
            from bucket at month N to bucket at month N+1
-------------------------------------------------------------------------*/

libname raw "/data/raw";
libname work_lib "/data/work";

/* 1. Load raw account-month extract (would normally come from
      Teradata/Snowflake via LIBNAME or SQL PassThrough) */
data work_lib.acct_month;
    set raw.account_month_delinquency;
run;

/* 2. Self-join current month to next month per account using PROC SQL,
      the same pattern used for DAQC remediation population joins */
proc sql;
    create table work_lib.roll_pairs as
    select
        a.account_id,
        a.month                    as month_from,
        a.delinquency_bucket       as bucket_from,
        b.month                    as month_to,
        b.delinquency_bucket       as bucket_to
    from work_lib.acct_month as a
    inner join work_lib.acct_month as b
        on a.account_id = b.account_id
       and b.month = a.month + 1;
quit;

/* 3. Roll-rate transition matrix: counts */
proc freq data=work_lib.roll_pairs noprint;
    tables bucket_from * bucket_to / out=work_lib.roll_rate_counts;
run;

/* 4. Convert counts to row-percentages (the actual "roll rate") */
proc sql;
    create table work_lib.roll_rate_matrix as
    select
        c.bucket_from,
        c.bucket_to,
        c.count,
        calculated pct_of_from_bucket
    from work_lib.roll_rate_counts as c,
         (select bucket_from as bf, sum(count) as total_from
          from work_lib.roll_rate_counts
          group by bucket_from) as t
    where c.bucket_from = t.bf
    ;
quit;

/* 5. Report: weekly/monthly portfolio dashboard input */
proc report data=work_lib.roll_rate_matrix nowd;
    columns bucket_from bucket_to count pct_of_from_bucket;
    define bucket_from / group "From Bucket";
    define bucket_to   / group "To Bucket";
    define count       / sum "Account Count";
    define pct_of_from_bucket / format=percent8.1 "Roll %";
run;

/* Notes for readers of the Python/R migrations:
   - The self-join in step 2 becomes a pandas .merge() on (account_id) with
     month offset by 1.
   - PROC FREQ's two-way table becomes pandas.crosstab().
   - The percent-of-row calc becomes a simple .div(rowsum, axis=0). */
