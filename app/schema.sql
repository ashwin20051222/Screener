-- ScreenerDesk DuckDB schema (Complete: prices, masters, classification, actions, F&O, ownership, filings, technicals, ETFs, quant scores)
-- Conventions: prices in Rs, volumes in shares, turnover in Rs (raw), financials & market-cap in Rs Cr.
-- All tables upserted idempotently by the stated primary key.

CREATE TABLE IF NOT EXISTS ref_security (
    security_id               VARCHAR PRIMARY KEY,   -- ISIN when known; else 'BSE:<code>' / 'NSE:<symbol>'
    isin                      VARCHAR,
    nse_symbol                VARCHAR,
    bse_code                  VARCHAR,
    name                      VARCHAR,
    nse_series                VARCHAR,
    bse_series                VARCHAR,
    listing_date              DATE,
    face_value                DOUBLE,
    paid_up_value             DOUBLE,
    market_lot                INTEGER,
    shares_outstanding        BIGINT,
    shares_source             VARCHAR,
    shares_as_of              DATE,
    sector                    VARCHAR,               -- Mapped UI sector (11 sectors + 'ETF')
    sub_sector                VARCHAR,               -- Detailed sub-sector / industry
    industry                  VARCHAR,               -- Raw exchange industry classification
    financial_template        VARCHAR DEFAULT 'industrials', -- industrials | utilities | banks | insurers
    is_financial_institution  BOOLEAN DEFAULT FALSE,
    is_etf                    BOOLEAN DEFAULT FALSE,
    is_sme                    BOOLEAN DEFAULT FALSE,
    fno_eligible              BOOLEAN DEFAULT FALSE,
    listing_status            VARCHAR DEFAULT 'listed',
    updated_at                TIMESTAMP DEFAULT current_timestamp
);

CREATE TABLE IF NOT EXISTS ref_index_constituent (
    index_name  VARCHAR NOT NULL,
    symbol      VARCHAR NOT NULL,
    company     VARCHAR,
    industry    VARCHAR,
    isin        VARCHAR,
    series      VARCHAR,
    as_of       DATE NOT NULL,
    PRIMARY KEY (index_name, symbol, as_of)
);

CREATE TABLE IF NOT EXISTS ref_amfi_classification (
    as_of_date      DATE NOT NULL,
    isin            VARCHAR NOT NULL,
    symbol          VARCHAR,
    company         VARCHAR,
    avg_mcap_crs    DOUBLE,
    rank            INTEGER,
    classification  VARCHAR,                -- Large | Mid | Small
    fetched_at      TIMESTAMP DEFAULT current_timestamp,
    PRIMARY KEY (as_of_date, isin)
);

CREATE TABLE IF NOT EXISTS ref_fno_lot (
    symbol      VARCHAR NOT NULL,
    lot_size    INTEGER,
    sao         VARCHAR,
    as_of       DATE NOT NULL,
    PRIMARY KEY (symbol, as_of)
);

CREATE TABLE IF NOT EXISTS ref_fbil_mibor (
    rate_date   DATE NOT NULL,
    tenor       VARCHAR NOT NULL,           -- 'mibor_3m'
    rate_pct    DOUBLE NOT NULL,
    source      VARCHAR DEFAULT 'manual (official FBIL public rate)',
    entered_at  TIMESTAMP DEFAULT current_timestamp,
    PRIMARY KEY (rate_date, tenor)
);

-- Prices ---------------------------------------------------------------
CREATE TABLE IF NOT EXISTS px_daily (
    source       VARCHAR NOT NULL,          -- 'NSE' | 'BSE'
    date         DATE NOT NULL,
    symbol       VARCHAR NOT NULL,
    isin         VARCHAR,
    series       VARCHAR,
    open         DOUBLE,
    high         DOUBLE,
    low          DOUBLE,
    close        DOUBLE,
    prev_close   DOUBLE,
    last         DOUBLE,
    volume       BIGINT,
    turnover_rs  DOUBLE,
    wap          DOUBLE,                    -- derived: turnover_rs / volume
    trades       BIGINT,
    PRIMARY KEY (source, symbol, date, series)
);

-- F&O daily (from UDiFF FO bhavcopy) --------------------------------------
CREATE TABLE IF NOT EXISTS fno_daily (
    source        VARCHAR NOT NULL,
    date          DATE NOT NULL,
    underlying    VARCHAR NOT NULL,
    expiry        DATE,
    actual_expiry DATE,
    instrument    VARCHAR,                  -- 'STF' futures | 'STO' options | 'IDX' index
    option_type   VARCHAR,                  -- 'CE' | 'PE' | '' for futures
    strike        DOUBLE,
    close         DOUBLE,
    prev_close    DOUBLE,
    settle_price  DOUBLE,
    oi            BIGINT,
    oi_change     BIGINT,
    volume        BIGINT,
    turnover_rs   DOUBLE,
    trades        BIGINT,
    new_lot       INTEGER,
    PRIMARY KEY (source, underlying, expiry, instrument, option_type, strike, date)
);

-- F&O derived daily metrics (Step 4.3) ------------------------------------
CREATE TABLE IF NOT EXISTS fno_metrics_daily (
    source                      VARCHAR NOT NULL,
    underlying                  VARCHAR NOT NULL,
    date                        DATE NOT NULL,
    lot_size                    INTEGER,
    future_close_price          DOUBLE,
    future_volume               BIGINT,
    future_open_interest        BIGINT,
    chg_1d_future_oi            DOUBLE,
    chg_1w_future_oi            DOUBLE,
    chg_1d_future_volume        DOUBLE,
    chg_1w_future_volume        DOUBLE,
    basis                       DOUBLE,
    fair_value                  DOUBLE,
    fair_value_spread           DOUBLE,
    cash_carry_profit           DOUBLE,
    rollover_cost               DOUBLE,
    percentage_rollover         DOUBLE,
    calendar_spread             DOUBLE,
    call_open_interest          BIGINT,
    put_open_interest           BIGINT,
    put_call_ratio              DOUBLE,
    chg_1d_call_oi              DOUBLE,
    chg_1w_call_oi              DOUBLE,
    chg_1d_put_oi               DOUBLE,
    chg_1w_put_oi               DOUBLE,
    highest_call_oi_strike      DOUBLE,
    highest_put_oi_strike       DOUBLE,
    highest_1d_oi_chg_ce_strike DOUBLE,
    highest_1d_oi_chg_pe_strike DOUBLE,
    highest_1w_oi_chg_ce_strike DOUBLE,
    highest_1w_oi_chg_pe_strike DOUBLE,
    fair_value_status           VARCHAR,    -- 'computed' | 'Unavailable: missing FBIL MIBOR'
    PRIMARY KEY (source, underlying, date)
);

CREATE TABLE IF NOT EXISTS corp_action (
    symbol         VARCHAR NOT NULL,
    isin           VARCHAR,
    company        VARCHAR,
    ex_date        DATE,
    record_date    DATE,
    purpose        VARCHAR,
    face_value     DOUBLE,
    broadcast_date DATE,
    source         VARCHAR DEFAULT 'NSE coa api',
    PRIMARY KEY (symbol, ex_date, purpose)
);

-- Ownership, Pledges & Deals (Step 4.4) -----------------------------------
CREATE TABLE IF NOT EXISTS ownership_quarterly (
    symbol                     VARCHAR NOT NULL,
    isin                       VARCHAR,
    quarter_end                DATE NOT NULL,
    promoter_pct               DOUBLE,
    promoter_pledged_pct       DOUBLE,      -- % of promoter shares pledged
    promoter_pledged_total_pct DOUBLE,      -- % of total equity pledged
    mf_pct                     DOUBLE,
    dii_pct                    DOUBLE,
    fii_pct                    DOUBLE,
    retail_pct                 DOUBLE,
    insurance_pct              DOUBLE,
    no_of_shareholders         BIGINT,
    source                     VARCHAR,
    fetched_at                 TIMESTAMP DEFAULT current_timestamp,
    PRIMARY KEY (symbol, quarter_end)
);

CREATE TABLE IF NOT EXISTS bulk_block_deals (
    deal_date   DATE NOT NULL,
    exchange    VARCHAR NOT NULL,           -- NSE | BSE
    deal_type   VARCHAR NOT NULL,           -- BULK | BLOCK
    symbol      VARCHAR NOT NULL,
    isin        VARCHAR,
    client_name VARCHAR NOT NULL,
    buy_sell    VARCHAR NOT NULL,           -- BUY | SELL
    quantity    BIGINT NOT NULL,
    price       DOUBLE,
    remarks     VARCHAR,
    source      VARCHAR,
    PRIMARY KEY (deal_date, exchange, deal_type, symbol, client_name, buy_sell, quantity)
);

CREATE TABLE IF NOT EXISTS insider_trades (
    broadcast_date       DATE NOT NULL,
    symbol               VARCHAR NOT NULL,
    isin                 VARCHAR,
    acquirer_name        VARCHAR NOT NULL,
    person_category      VARCHAR,
    transaction_type     VARCHAR NOT NULL,  -- BUY | SELL
    shares               BIGINT NOT NULL,
    trade_value          DOUBLE,
    after_holding_shares BIGINT,
    after_holding_pct    DOUBLE,
    source               VARCHAR,
    PRIMARY KEY (broadcast_date, symbol, acquirer_name, transaction_type, shares)
);

-- Financial Statements & Quarantine (Step 4.5) ----------------------------
CREATE TABLE IF NOT EXISTS fin_annual (
    symbol                      VARCHAR NOT NULL,
    isin                        VARCHAR,
    fiscal_year_end             DATE NOT NULL,
    period_months               INTEGER DEFAULT 12,
    statement_type              VARCHAR NOT NULL, -- 'consolidated' | 'standalone'
    template_type               VARCHAR DEFAULT 'industrials',
    -- Income Statement (Rs Cr, except EPS/DPS in Rs)
    total_revenue               DOUBLE,
    cost_of_revenue             DOUBLE,
    cost_of_goods_sold          DOUBLE,
    gross_profit                DOUBLE,
    ebitda                      DOUBLE,
    depreciation_amortization   DOUBLE,
    pbit                        DOUBLE,
    interest_expense            DOUBLE,
    pbt                         DOUBLE,
    taxes                       DOUBLE,
    net_income                  DOUBLE,
    eps                         DOUBLE,
    dps                         DOUBLE,
    power_fuel_cost             DOUBLE,
    raw_materials               DOUBLE,
    employee_cost               DOUBLE,
    sga_expense                 DOUBLE,
    rd_expense                  DOUBLE,
    operating_other_expenses    DOUBLE,
    interest_income             DOUBLE,
    net_interest_income         DOUBLE,
    loan_loss_provision         DOUBLE,
    -- Balance Sheet (Rs Cr, shares in count)
    cash_and_st_inv             DOUBLE,
    total_receivables           DOUBLE,
    total_inventory             DOUBLE,
    other_current_assets        DOUBLE,
    total_current_assets        DOUBLE,
    gross_loans                 DOUBLE,
    npa_provisions              DOUBLE,
    net_loans                   DOUBLE,
    net_ppe                     DOUBLE,
    goodwill_intangibles        DOUBLE,
    long_term_investments       DOUBLE,
    other_assets                DOUBLE,
    total_assets                DOUBLE,
    accounts_payable            DOUBLE,
    total_deposits              DOUBLE,
    other_current_liabilities   DOUBLE,
    total_current_liabilities   DOUBLE,
    total_long_term_debt        DOUBLE,
    total_debt                  DOUBLE,
    deferred_income_tax         DOUBLE,
    minority_interest           DOUBLE,
    other_liabilities           DOUBLE,
    total_liabilities           DOUBLE,
    common_stock                DOUBLE,
    apic                        DOUBLE,
    retained_earnings           DOUBLE,
    other_equity                DOUBLE,
    total_equity                DOUBLE,
    common_shares_out           BIGINT,
    preferred_shares_out        BIGINT,
    policy_liabilities          DOUBLE,
    -- Cash Flow (Rs Cr)
    changes_working_capital     DOUBLE,
    cfo                         DOUBLE,
    capex                       DOUBLE,
    cfi                         DOUBLE,
    dividends_paid              DOUBLE,
    cff                         DOUBLE,
    fx_effects                  DOUBLE,
    net_change_cash             DOUBLE,
    source                      VARCHAR,
    raw_file_sha                VARCHAR,
    filing_url                  VARCHAR,
    filing_date                 DATE,
    parser_version              VARCHAR,
    PRIMARY KEY (symbol, fiscal_year_end, statement_type)
);

CREATE TABLE IF NOT EXISTS fin_quarterly (
    symbol                     VARCHAR NOT NULL,
    isin                       VARCHAR,
    quarter_end                DATE NOT NULL,
    statement_type             VARCHAR NOT NULL,
    total_revenue_q            DOUBLE,
    ebitda_q                   DOUBLE,
    operating_other_expenses_q DOUBLE,
    pbit_q                     DOUBLE,
    pbt_q                      DOUBLE,
    net_income_q               DOUBLE,
    eps_q                      DOUBLE,
    source                     VARCHAR,
    filing_url                 VARCHAR,
    filing_date                DATE,
    parser_version             VARCHAR,
    PRIMARY KEY (symbol, quarter_end, statement_type)
);

CREATE TABLE IF NOT EXISTS fin_quarantine (
    symbol          VARCHAR NOT NULL,
    fiscal_year_end DATE NOT NULL,
    statement_type  VARCHAR NOT NULL,
    reason          VARCHAR NOT NULL,
    total_assets    DOUBLE,
    total_liabilities DOUBLE,
    total_equity    DOUBLE,
    diff            DOUBLE,
    quarantined_at  TIMESTAMP DEFAULT current_timestamp,
    PRIMARY KEY (symbol, fiscal_year_end, statement_type)
);

-- Technicals Daily Snapshot (Step 4.6) ------------------------------------
CREATE TABLE IF NOT EXISTS tech_daily (
    symbol              VARCHAR NOT NULL,
    date                DATE NOT NULL,
    close_adj           DOUBLE,
    sma_10d             DOUBLE,
    sma_50d             DOUBLE,
    sma_100d            DOUBLE,
    sma_200d            DOUBLE,
    ema_10d             DOUBLE,
    ema_50d             DOUBLE,
    ema_100d            DOUBLE,
    ema_200d            DOUBLE,
    price_above_1m_sma  DOUBLE,
    price_above_12m_sma DOUBLE,
    price_above_1m_ema  DOUBLE,
    rsi_14d             DOUBLE,
    rsi_exp_14d         DOUBLE,
    adx_rating          DOUBLE,
    plus_di_14          DOUBLE,
    minus_di_14         DOUBLE,
    macd_line_1         DOUBLE,
    macd_line_2         DOUBLE,
    from_upper_bb       DOUBLE,
    from_lower_bb       DOUBLE,
    from_parabolic_sar  DOUBLE,
    williams_r          DOUBLE,
    stochastic_k        DOUBLE,
    stochastic_d        DOUBLE,
    chg_1w_obv          DOUBLE,
    chg_1w_ad_line      DOUBLE,
    super_trend         DOUBLE,
    supertrend_signal   INTEGER,            -- 1 buy | -1 sell
    max_loss_1y         DOUBLE,
    volatility          DOUBLE,
    volatility_vs_nifty DOUBLE,
    beta                DOUBLE,
    alpha               DOUBLE,
    sharpe_ratio        DOUBLE,
    relative_volume     DOUBLE,
    ret_1d              DOUBLE,
    ret_1w              DOUBLE,
    ret_1m              DOUBLE,
    ret_6m              DOUBLE,
    ret_1y              DOUBLE,
    cagr_5y             DOUBLE,
    ret_1w_vs_nifty     DOUBLE,
    ret_1m_vs_nifty     DOUBLE,
    ret_6m_vs_nifty     DOUBLE,
    ret_1y_vs_nifty     DOUBLE,
    away_52w_high       DOUBLE,
    away_52w_low        DOUBLE,
    avg_vol_1m          DOUBLE,
    avg_vol_3m          DOUBLE,
    chg_1d_volume       DOUBLE,
    chg_1w_volume       DOUBLE,
    PRIMARY KEY (symbol, date)
);

-- ETFs & NAV (Step 4.7) ---------------------------------------------------
CREATE TABLE IF NOT EXISTS etf_meta (
    symbol          VARCHAR PRIMARY KEY,
    isin            VARCHAR,
    scheme_code     VARCHAR,
    scheme_name     VARCHAR,
    benchmark_index VARCHAR,
    expense_ratio   DOUBLE,
    ter_as_of       DATE,
    tracking_error  DOUBLE,
    te_as_of        DATE,
    source          VARCHAR
);

CREATE TABLE IF NOT EXISTS etf_nav_daily (
    scheme_code VARCHAR NOT NULL,
    isin        VARCHAR,
    nav_date    DATE NOT NULL,
    scheme_name VARCHAR,
    nav         DOUBLE,
    source      VARCHAR,
    PRIMARY KEY (scheme_code, nav_date)
);

-- Quant Scores (Phase 5) --------------------------------------------------
CREATE TABLE IF NOT EXISTS quant_scores (
    symbol                        VARCHAR NOT NULL,
    as_of_date                    DATE NOT NULL,
    price_momentum_rank           DOUBLE,
    earnings_quality_rank         DOUBLE,
    price_to_intrinsic_value_rank DOUBLE,
    value_momentum_rank           DOUBLE,
    fundamental_score             DOUBLE,
    badge                         VARCHAR DEFAULT 'Approximate - computed locally',
    PRIMARY KEY (symbol, as_of_date)
);

CREATE TABLE IF NOT EXISTS raw_files (
    sha256     VARCHAR PRIMARY KEY,
    source     VARCHAR,
    url        VARCHAR,
    saved_path VARCHAR,
    bytes      BIGINT,
    rows       BIGINT,
    http_code  INTEGER,
    fetched_at TIMESTAMP DEFAULT current_timestamp,
    notes      VARCHAR
);

CREATE TABLE IF NOT EXISTS ingest_status (
    id          VARCHAR PRIMARY KEY,        -- job::run_marker unique
    job         VARCHAR,
    run_date    DATE,
    status      VARCHAR,                    -- ok | fail | skip | partial
    rows        BIGINT,
    message     VARCHAR,
    started_at  TIMESTAMP,
    finished_at TIMESTAMP
);

CREATE TABLE IF NOT EXISTS ingest_progress (
    job        VARCHAR NOT NULL,
    item_key   VARCHAR NOT NULL,
    status     VARCHAR NOT NULL,            -- ok | holiday | skip | fail
    message    VARCHAR,
    updated_at TIMESTAMP DEFAULT current_timestamp,
    PRIMARY KEY (job, item_key)
);

CREATE TABLE IF NOT EXISTS screener_snapshot (
    security_id     VARCHAR PRIMARY KEY,
    nse_symbol      VARCHAR,
    metrics_json    VARCHAR NOT NULL,
    provenance_json VARCHAR,
    built_at        TIMESTAMP DEFAULT current_timestamp
);

CREATE TABLE IF NOT EXISTS screener_snapshot_meta (
    id             VARCHAR PRIMARY KEY,
    synced         BOOLEAN NOT NULL,
    row_count      BIGINT NOT NULL,
    etag           VARCHAR NOT NULL,
    universes_json VARCHAR NOT NULL,
    as_of_json     VARCHAR NOT NULL,
    version        BIGINT DEFAULT 1,
    built_at       TIMESTAMP DEFAULT current_timestamp
);

CREATE TABLE IF NOT EXISTS data_jobs (
    job_id           VARCHAR PRIMARY KEY,
    sync_job         VARCHAR NOT NULL,
    filter_ids_json  VARCHAR,
    universe         VARCHAR,
    status           VARCHAR NOT NULL,       -- queued | running | completed | partial | blocked | error
    processed        INTEGER DEFAULT 0,
    total            INTEGER DEFAULT 0,
    progress_pct     DOUBLE DEFAULT 0.0,
    message          VARCHAR,
    error            VARCHAR,
    snapshot_version BIGINT,
    started_at       TIMESTAMP DEFAULT current_timestamp,
    updated_at       TIMESTAMP DEFAULT current_timestamp,
    finished_at      TIMESTAMP
);