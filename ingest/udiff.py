"""UDiFF common bhavcopy parsing (NSE + BSE share the same 34-column layout).

Verified 2026-10-25 against live files of trade date 2026-10-23:
  NSE CM : BhavCopy_NSE_CM_0_0_0_20261023_F_0000.csv.zip  (3,730 rows; SctySrs EQ/GB/...)
  NSE FO : BhavCopy_NSE_FO_0_0_0_20261023_F_0000.csv.zip  (40,212 rows; STF/STO)
  BSE CM : BhavCopy_BSE_CM_0_0_0_20261023_F_0000.CSV      (plain CSV, same headers)

Columns (both venues):
  TradDt,BizDt,Sgmt,Src,FinInstrmTp,FinInstrmId,ISIN,TckrSymb,SctySrs,XpryDt,
  FininstrmActlXpryDt,StrkPric,OptnTp,FinInstrmNm,OpnPric,HghPric,LwPric,ClsPric,
  LastPric,PrvsClsgPric,UndrlygPric,SttlmPric,OpnIntrst,ChngInOpnIntrst,TtlTradgVol,
  TtlTrfVal,TtlNbOfTxsExctd,SsnId,NewBrdLotQty,Rmks,Rsvd1..Rsvd4

Note: NSE CM UDiFF has NO VWAP column; day VWAP is derived (mission 7.5):
    wap = TtlTrfVal / TtlTradgVol  (traded value Rs / traded qty)
"""
from __future__ import annotations

import csv
import io
import logging
import zipfile
from datetime import date, datetime

log = logging.getLogger(__name__)

REQUIRED = ["TradDt", "TckrSymb", "SctySrs", "ClsPric"]
LEGACY_CM_REQUIRED = ["SYMBOL", "SERIES", "CLOSE", "TIMESTAMP"]


def _num(v: str):
    v = (v or "").strip()
    if v in ("", "-"):
        return None
    try:
        return float(v)
    except ValueError:
        return None


def _int(v: str):
    f = _num(v)
    return None if f is None else int(f)


def _dt(v: str):
    v = (v or "").strip()
    if not v:
        return None
    for fmt in ("%Y-%m-%d", "%d-%b-%Y", "%d/%m/%Y"):
        try:
            return datetime.strptime(v, fmt).date()
        except ValueError:
            continue
    return None


def _detect_layout(header: list[str]) -> str:
    hset = set(header)
    if all(c in hset for c in REQUIRED):
        return "udiff"
    if all(c in hset for c in LEGACY_CM_REQUIRED):
        return "legacy_cm"
    missing = [c for c in REQUIRED if c not in hset]
    raise ValueError(f"Bhavcopy file missing columns: {missing}; got {header[:12]}...")


def read_bhav_bytes(payload: bytes | str) -> list[list[str]]:
    """Extract CSV rows from a UDiFF or Legacy NSE CM bhavcopy (zip or plain CSV)."""
    if isinstance(payload, str):
        payload = payload.encode("utf-8", "replace")
    if payload[:2] == b"PK":
        with zipfile.ZipFile(io.BytesIO(payload)) as z:
            inner = z.namelist()[0]
            text = z.read(inner).decode("utf-8", "replace")
    else:
        text = payload.decode("utf-8", "replace")
    rows = list(csv.reader(io.StringIO(text)))
    if not rows:
        raise ValueError("empty bhavcopy file")
    header = [h.strip() for h in rows[0]]
    _detect_layout(header)
    return rows


def parse_udiff(
    payload: bytes,
    *,
    source: str,
    series_keep: list[str] | None = None,
    fo_mode: bool = False,
) -> dict:
    """Parse one UDiFF bhavcopy into canonical row-dicts.

    fo_mode=False -> px_daily rows (cash market; instrument rows with an expiry/strike are skipped)
    fo_mode=True  -> fno_daily rows (derivatives)
    `series_keep` limits CM rows to given equity series (None = keep all, filter at caller).
    """
    rows = read_bhav_bytes(payload)
    header = [h.strip() for h in rows[0]]
    layout = _detect_layout(header)
    idx = {c: i for i, c in enumerate(header)}

    px_rows: list[dict] = []
    fno_rows: list[dict] = []
    skipped = 0
    seen_series: dict[str, int] = {}

    if layout == "legacy_cm":
        if fo_mode:
            raise ValueError("Legacy CM bhavcopy cannot be parsed in F&O mode")
        for r in rows[1:]:
            get = lambda c: (r[idx[c]] if c in idx and idx[c] < len(r) else "")
            trad_dt = _dt(get("TIMESTAMP"))
            symbol = get("SYMBOL").strip()
            series = get("SERIES").strip()
            cls_px = _num(get("CLOSE"))
            if trad_dt is None or not symbol or cls_px is None:
                skipped += 1
                continue
            seen_series[series] = seen_series.get(series, 0) + 1
            if series_keep is not None and series not in series_keep:
                skipped += 1
                continue
            volume = _int(get("TOTTRDQTY"))
            turnover = _num(get("TOTTRDVAL"))
            wap = round(turnover / volume, 4) if (volume and volume > 0 and turnover is not None) else None
            px_rows.append({
                "source": source,
                "date": trad_dt,
                "symbol": symbol,
                "isin": get("ISIN").strip() or None,
                "series": series or None,
                "open": _num(get("OPEN")),
                "high": _num(get("HIGH")),
                "low": _num(get("LOW")),
                "close": cls_px,
                "prev_close": _num(get("PREVCLOSE")),
                "last": _num(get("LAST")),
                "volume": volume,
                "turnover_rs": turnover,
                "wap": wap,
                "trades": _int(get("TOTALTRADES")),
            })
        return {"px_rows": px_rows, "fno_rows": [], "skipped": skipped, "series_counts": seen_series}

    for r in rows[1:]:
        get = lambda c: (r[idx[c]] if c in idx and idx[c] < len(r) else "")
        trad_dt = _dt(get("TradDt"))
        symbol = get("TckrSymb").strip()
        series = get("SctySrs").strip()
        opn = _num(get("OpnPric"))
        strike = _num(get("StrkPric"))
        opt_tp = get("OptnTp").strip().upper() or None

        if trad_dt is None or not symbol or _num(get("ClsPric")) is None:
            skipped += 1
            continue

        if fo_mode:
            if not get("XpryDt"):
                skipped += 1
                continue
            fno_rows.append({
                "source": source,
                "date": trad_dt,
                "underlying": symbol,
                "expiry": _dt(get("XpryDt")),
                "actual_expiry": _dt(get("FininstrmActlXpryDt")),
                "instrument": get("FinInstrmTp").strip().upper() or None,
                "option_type": opt_tp,
                "strike": strike,
                "close": _num(get("ClsPric")),
                "prev_close": _num(get("PrvsClsgPric")),
                "settle_price": _num(get("SttlmPric")),
                "oi": _int(get("OpnIntrst")),
                "oi_change": _int(get("ChngInOpnIntrst")),
                "volume": _int(get("TtlTradgVol")),
                "turnover_rs": _num(get("TtlTrfVal")),
                "trades": _int(get("TtlNbOfTxsExctd")),
                "new_lot": _int(get("NewBrdLotQty")),
            })
        else:
            # Cash market: rows carrying option strikes/expiry belong to derivatives (skip here)
            if get("XpryDt") or opt_tp:
                skipped += 1
                continue
            seen_series[series] = seen_series.get(series, 0) + 1
            if series_keep is not None and series not in series_keep:
                skipped += 1
                continue
            volume = _int(get("TtlTradgVol"))
            turnover = _num(get("TtlTrfVal"))
            wap = None
            if volume and volume > 0 and turnover is not None:
                wap = round(turnover / volume, 4)
            px_rows.append({
                "source": source,
                "date": trad_dt,
                "symbol": symbol,
                "isin": get("ISIN").strip() or None,
                "series": series or None,
                "open": opn,
                "high": _num(get("HghPric")),
                "low": _num(get("LwPric")),
                "close": _num(get("ClsPric")),
                "prev_close": _num(get("PrvsClsgPric")),
                "last": _num(get("LastPric")),
                "volume": volume,
                "turnover_rs": turnover,
                "wap": wap,
                "trades": _int(get("TtlNbOfTxsExctd")),
            })

    return {"px_rows": px_rows, "fno_rows": fno_rows, "skipped": skipped, "series_counts": seen_series}
