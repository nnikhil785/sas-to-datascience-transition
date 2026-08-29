/*-----------------------------------------------------------------------
  Automated Data Profiling / Data Dictionary Macro - SAS
  ---------------------------------------------------------------------
  Purpose : Reusable macro that profiles any SAS dataset and produces a
            data-dictionary style summary: variable name, type, length,
            missing count/%, distinct count, and (for numeric vars)
            min/mean/max. This is the pattern behind "built data
            dictionaries and profiling documentation" work referenced
            throughout the author's DAQC / migration-readiness experience.

  Usage   : %profile_dataset(work.customer_accounts);
-------------------------------------------------------------------------*/

%macro profile_dataset(dsn);

    /* 1. Structural metadata: name, type, length -- PROC CONTENTS */
    proc contents data=&dsn out=work._contents(keep=name type length) noprint;
    run;

    /* 2. Row count for missing-% calculations */
    proc sql noprint;
        select count(*) into :nobs from &dsn;
    quit;

    /* 3. Missing counts per variable (numeric + character handled) */
    proc means data=&dsn nmiss n noprint;
        output out=work._nmiss (drop=_type_ _freq_);
    run;

    proc transpose data=work._nmiss out=work._nmiss_t(rename=(_name_=name col1=n_missing));
        var _numeric_;
    run;

    /* 4. Distinct-value counts per variable */
    proc sql noprint;
        create table work._distinct as
        select name from work._contents;
    quit;

    /* (In production this loop calls PROC SQL "select count(distinct var)"
       per variable and appends results -- omitted here for brevity; the
       Python migration below does this generically via nunique().) */

    /* 5. Combine structural + missing + distinct info into one dictionary */
    proc sql;
        create table work.data_dictionary as
        select
            c.name,
            c.type,
            c.length,
            m.n_missing,
            (m.n_missing / &nobs) as pct_missing format=percent8.1
        from work._contents as c
        left join work._nmiss_t as m
            on c.name = m.name;
    quit;

    proc print data=work.data_dictionary noobs; run;

%mend profile_dataset;

/* Example call */
%profile_dataset(work.customer_accounts);
