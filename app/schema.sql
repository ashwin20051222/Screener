-- ScreenerDesk DuckDB schema (Step 2: prices, master, classification, actions, status)
-- Conventions: prices in Rs, volumes in shares, turnover in Rs (raw), market-cap in Rs Cr computed later.
-- All tables upserted idempotently by the stated primary key.

CREATE TABLE IF NOT EXISTS ref_security (
    security_id     VARCHAR PRIMARY KEY,   -- ISIN when known; else 'BSE:<code>' / 'SME:<symbol>'
    isin            VARCHAR,
    nse_symbol      VARCHAR,
    bse_code        VARCHAR,
    name            VARCHAR,
    nse_series      VARCHAR,
    bse_series      VARCHAR,
    listing_date    DATE,
    face_value      DOUBLE,
    paid_up_value   DOUBLE,
    market_lot      INTEGER,
    is_etf          BOOLEAN DEFAULT FALSE,
    is_sme          BOOLEAN DEFAULT FALSE,
    fno_eligible    BOOLEAN DEFAULT FALSE,
    listing_status  VARCHAR DEFAULT 'listed',
    updated_at      TIMESTAMP DEFAULT current_timestamp
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
    as_of_date      DATE NOT NULL,          -- period end the average MC list is titled by (e.g. 2026-06-30)
    isin            VARCHAR NOT NULL,
    symbol          VARCHAR,
    company         VARCHAR,
    avg_mcap_crs    DOUBLE,                 -- average market capitalisation, Rs Cr (AMFI's own basis)
    rank            INTEGER,
    classification  VARCHAR,                -- Large | Mid | Small
    fetched_at      TIMESTAMP DEFAULT current_timestamp,
    PRIMARY KEY (as_of_date, isin)
);

CREATE TABLE IF NOT EXISTS ref_fno_lot (
    symbol      VARCHAR NOT NULL,
    lot_size    INTEGER,
    sao          DOUBLE,                    -- surveillance action tag if provided in the lot file
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
    source       VARCHAR NOT NULL,          -- 'NSE' | 'BSE' (exchange the quote belongs to)
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
    wap          DOUBLE,                    -- derived: turnover_rs / volume (mission: day VWAP = traded value / traded qty)
    trades       BIGINT,
    PRIMARY KEY (source, symbol, date, series)
);

-- F&O daily (from UDiFF FO bhavcopy) --------------------------------------
CREATE TABLE IF NOT EXISTS fno_daily (
    source       VARCHAR NOT NULL,
    date         DATE NOT NULL,
    underlying   VARCHAR NOT NULL,
    expiry       DATE,
    actual_expiry DATE,
    instrument   VARCHAR,                   -- 'STF' futures | 'STO' options | 'IDX' index
    option_type  VARCHAR,                   -- 'CE' | 'PE' | NULL for futures
    strike       DOUBLE,
    close        DOUBLE,
    prev_close   DOUBLE,
    settle_price DOUBLE,
    oi           BIGINT,
    oi_change    BIGINT,
    volume       BIGINT,
    turnover_rs  DOUBLE,
    trades       BIGINT,
    new_lot      INTEGER,
    PRIMARY KEY (source, underlying, expiry, instrument, option_type, strike, date)
);

CREATE TABLE IF NOT EXISTS corp_action (
    symbol      VARCHAR NOT NULL,
    isin        VARCHAR,
    company     VARCHAR,
    ex_date     DATE,
    record_date DATE,
    purpose     VARCHAR,
    face_value  DOUBLE,
    broadcast_date DATE,
    source      VARCHAR DEFAULT 'NSE coa api',
    PRIMARY KEY (symbol, ex_date, purpose)
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
