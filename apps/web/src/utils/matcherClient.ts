import { MatchRecord, MatchReport, PnLData, StockRow } from '../types';

export interface MasterSecurity {
  isin: string;
  nse_symbol: string;
  bse_code: string;
  name: string;
  sector: string;
  sub_sector: string;
  close_price: number;
  market_cap: number;
  pe_ratio?: number | null;
  return_on_equity?: number | null;
}

export const CLIENT_MASTER_SECURITIES: MasterSecurity[] = [
  { isin: 'INE002A01018', nse_symbol: 'RELIANCE', bse_code: '500325', name: 'Reliance Industries Limited', sector: 'Energy', sub_sector: 'Oil & Gas - Refining & Marketing', close_price: 2420.50, market_cap: 1639061.09, pe_ratio: 24.50, return_on_equity: 8.95 },
  { isin: 'INE467B01029', nse_symbol: 'TCS', bse_code: '532540', name: 'Tata Consultancy Services Limited', sector: 'Information Technology', sub_sector: 'IT Services & Consulting', close_price: 3150.00, market_cap: 1150000.00, pe_ratio: 27.80, return_on_equity: 43.50 },
  { isin: 'INE040A01034', nse_symbol: 'HDFCBANK', bse_code: '500180', name: 'HDFC Bank Limited', sector: 'Financials', sub_sector: 'Private Banks', close_price: 1450.00, market_cap: 900000.00, pe_ratio: 18.20, return_on_equity: 16.20 },
  { isin: 'INE090A01021', nse_symbol: 'ICICIBANK', bse_code: '532174', name: 'ICICI Bank Limited', sector: 'Financials', sub_sector: 'Private Banks', close_price: 930.00, market_cap: 650000.00, pe_ratio: 16.90, return_on_equity: 15.80 },
  { isin: 'INE009A01021', nse_symbol: 'INFY', bse_code: '500209', name: 'Infosys Limited', sector: 'Information Technology', sub_sector: 'IT Services & Consulting', close_price: 1400.00, market_cap: 580000.00, pe_ratio: 23.40, return_on_equity: 29.10 },
  { isin: 'INE030A01027', nse_symbol: 'HINDUNILVR', bse_code: '500696', name: 'Hindustan Unilever Limited', sector: 'Consumer Staples', sub_sector: 'FMCG - Household Products', close_price: 2350.00, market_cap: 550000.00, pe_ratio: 54.20, return_on_equity: 20.40 },
  { isin: 'INE154A01025', nse_symbol: 'ITC', bse_code: '500875', name: 'ITC Limited', sector: 'Consumer Staples', sub_sector: 'FMCG - Tobacco', close_price: 415.00, market_cap: 520000.00, pe_ratio: 26.50, return_on_equity: 27.80 },
  { isin: 'INE062A01020', nse_symbol: 'SBIN', bse_code: '500112', name: 'State Bank of India', sector: 'Financials', sub_sector: 'Public Banks', close_price: 560.00, market_cap: 500000.00, pe_ratio: 9.80, return_on_equity: 16.50 },
  { isin: 'INE397D01024', nse_symbol: 'BHARTIARTL', bse_code: '532454', name: 'Bharti Airtel Limited', sector: 'Communication Services', sub_sector: 'Telecom Services', close_price: 820.00, market_cap: 480000.00, pe_ratio: 72.10, return_on_equity: 12.30 },
  { isin: 'INE018A01030', nse_symbol: 'LT', bse_code: '500510', name: 'Larsen & Toubro Limited', sector: 'Industrials', sub_sector: 'Construction & Engineering', close_price: 2950.00, market_cap: 420000.00, pe_ratio: 38.20, return_on_equity: 14.70 },
  { isin: 'INE214T01019', nse_symbol: 'LTTS', bse_code: '540115', name: 'L&T Technology Services Limited', sector: 'Information Technology', sub_sector: 'IT Services & Consulting', close_price: 4850.00, market_cap: 52000.00, pe_ratio: 36.50, return_on_equity: 22.00 },
  { isin: 'INE498L01015', nse_symbol: 'LTF', bse_code: '533519', name: 'L&T Finance Limited', sector: 'Financials', sub_sector: 'NBFC', close_price: 170.00, market_cap: 42000.00, pe_ratio: 17.50, return_on_equity: 11.20 },
  { isin: 'INE296A01024', nse_symbol: 'BAJFINANCE', bse_code: '500034', name: 'Bajaj Finance Limited', sector: 'Financials', sub_sector: 'NBFC', close_price: 6800.00, market_cap: 410000.00, pe_ratio: 31.40, return_on_equity: 23.50 },
  { isin: 'INE021A01026', nse_symbol: 'ASIANPAINT', bse_code: '500820', name: 'Asian Paints Limited', sector: 'Materials', sub_sector: 'Paints', close_price: 3050.00, market_cap: 290000.00, pe_ratio: 52.00, return_on_equity: 26.00 },
  { isin: 'INE585B01010', nse_symbol: 'MARUTI', bse_code: '532500', name: 'Maruti Suzuki India Limited', sector: 'Consumer Discretionary', sub_sector: 'Auto - 4 Wheelers', close_price: 9250.00, market_cap: 280000.00, pe_ratio: 29.50, return_on_equity: 13.90 },
  { isin: 'INE280A01028', nse_symbol: 'TITAN', bse_code: '500114', name: 'Titan Company Limited', sector: 'Consumer Discretionary', sub_sector: 'Gems, Jewellery & Watches', close_price: 2980.00, market_cap: 260000.00, pe_ratio: 78.40, return_on_equity: 30.20 },
  { isin: 'INE044A01036', nse_symbol: 'SUNPHARMA', bse_code: '524715', name: 'Sun Pharmaceutical Industries Limited', sector: 'Health Care', sub_sector: 'Pharmaceuticals', close_price: 1050.00, market_cap: 250000.00, pe_ratio: 32.10, return_on_equity: 15.00 },
  { isin: 'INE155A01022', nse_symbol: 'TATAMOTORS', bse_code: '500570', name: 'Tata Motors Limited', sector: 'Consumer Discretionary', sub_sector: 'Auto - 4 Wheelers', close_price: 650.00, market_cap: 240000.00, pe_ratio: 14.20, return_on_equity: 18.00 },
  { isin: 'IN9155A01020', nse_symbol: 'TATAMTRDVR', bse_code: '570001', name: 'Tata Motors Limited', sector: 'Consumer Discretionary', sub_sector: 'Auto - 4 Wheelers', close_price: 450.00, market_cap: 18000.00, pe_ratio: 12.10, return_on_equity: 18.00 },
  { isin: 'INE081A01012', nse_symbol: 'TATASTEEL', bse_code: '500470', name: 'Tata Steel Limited', sector: 'Materials', sub_sector: 'Steel & Iron Products', close_price: 125.00, market_cap: 150000.00, pe_ratio: 11.20, return_on_equity: 10.50 },
  { isin: 'INE238A01034', nse_symbol: 'AXISBANK', bse_code: '532215', name: 'Axis Bank Limited', sector: 'Financials', sub_sector: 'Private Banks', close_price: 970.00, market_cap: 290000.00, pe_ratio: 13.50, return_on_equity: 16.80 },
  { isin: 'INE075A01022', nse_symbol: 'WIPRO', bse_code: '507685', name: 'Wipro Limited', sector: 'Information Technology', sub_sector: 'IT Services & Consulting', close_price: 410.00, market_cap: 210000.00, pe_ratio: 19.50, return_on_equity: 14.20 },
  { isin: 'INE121A01024', nse_symbol: 'HCLTECH', bse_code: '532281', name: 'HCL Technologies Limited', sector: 'Information Technology', sub_sector: 'IT Services & Consulting', close_price: 1180.00, market_cap: 310000.00, pe_ratio: 21.00, return_on_equity: 22.50 },
  { isin: 'INE257A01026', nse_symbol: 'BHEL', bse_code: '500103', name: 'Bharat Heavy Electricals Limited', sector: 'Industrials', sub_sector: 'Heavy Electrical Equipment', close_price: 102.00, market_cap: 35000.00, pe_ratio: 45.00, return_on_equity: 2.50 },
  { isin: 'INE111A01025', nse_symbol: 'POWERGRID', bse_code: '532898', name: 'Power Grid Corporation of India Limited', sector: 'Utilities', sub_sector: 'Electric Utilities', close_price: 200.00, market_cap: 18000.00, pe_ratio: 12.00, return_on_equity: 18.20 },
  { isin: 'INE733E01010', nse_symbol: 'NTPC', bse_code: '532555', name: 'NTPC Limited', sector: 'Utilities', sub_sector: 'Electric Utilities', close_price: 210.00, market_cap: 190000.00, pe_ratio: 11.50, return_on_equity: 13.00 },
  { isin: 'INF204KB14I2', nse_symbol: 'NIFTYBEES', bse_code: '590101', name: 'Nippon India ETF Nifty BeES', sector: 'ETF', sub_sector: 'Index ETF', close_price: 240.50, market_cap: 25000.00, pe_ratio: null, return_on_equity: null },
  { isin: 'INF204KB17I5', nse_symbol: 'GOLDBEES', bse_code: '590095', name: 'Nippon India ETF Gold BeES', sector: 'ETF', sub_sector: 'Commodity ETF', close_price: 55.20, market_cap: 12000.00, pe_ratio: null, return_on_equity: null },
];

export function normalizeCompanyName(name: string): string {
  if (!name) return '';
  let s = name.toLowerCase();
  s = s.replace(/\(.*?\)/g, '');
  const suffixes = [
    /\bltd\b/g, /\blimited\b/g, /\bpvt\b/g, /\bprivate\b/g,
    /\binc\b/g, /\bincorporated\b/g, /\bcorp\b/g, /\bcorporation\b/g,
    /\bco\b/g, /\bcompany\b/g, /\bllp\b/g, /\bindustries\b/g,
    /\bholdings\b/g, /\benterprises?\b/g,
  ];
  for (const suf of suffixes) {
    s = s.replace(suf, '');
  }
  s = s.replace(/[^\w\s]/g, ' ');
  return s.split(/\s+/).filter(Boolean).join(' ').trim();
}

export function computeClientPnL(
  row: Record<string, any>,
  closePrice: number,
  qtyCol = 'quantity',
  buyPriceCol = 'buy_price'
): PnLData {
  let qty: number | null = null;
  let buy: number | null = null;

  // Search quantity aliases
  for (const k of [qtyCol, 'Quantity', 'quantity', 'qty', 'Qty', 'shares', 'Shares', 'units', 'Units']) {
    if (k in row && row[k] !== '' && row[k] !== null) {
      const parsed = parseFloat(String(row[k]).replace(/,/g, ''));
      if (!isNaN(parsed)) {
        qty = parsed;
        break;
      }
    }
  }

  // Search buy price aliases
  for (const k of [buyPriceCol, 'Buy_Price', 'Buy Price', 'buy_price', 'purchase_price', 'cost', 'Cost', 'avg_price']) {
    if (k in row && row[k] !== '' && row[k] !== null) {
      const parsed = parseFloat(String(row[k]).replace(/,/g, ''));
      if (!isNaN(parsed) && parsed > 0) {
        buy = parsed;
        break;
      }
    }
  }

  if (qty === null || buy === null || closePrice <= 0) {
    return { quantity: qty, buy_price: buy, invested_value: null, current_value: null, pnl_amount: null, pnl_pct: null };
  }

  const invested = qty * buy;
  const current = qty * closePrice;
  const pnlAmt = current - invested;
  const pnlPct = ((closePrice / buy) - 1.0) * 100.0;

  return {
    quantity: qty,
    buy_price: buy,
    invested_value: Math.round(invested * 100) / 100,
    current_value: Math.round(current * 100) / 100,
    pnl_amount: Math.round(pnlAmt * 100) / 100,
    pnl_pct: Math.round(pnlPct * 100) / 100,
  };
}

export function matchUniverseClient(
  rows: Record<string, any>[],
  idCol?: string | null,
  masterSecurities: MasterSecurity[] = CLIENT_MASTER_SECURITIES
): MatchReport {
  const matched: MatchRecord[] = [];
  const ambiguous: MatchRecord[] = [];
  const unmatched: MatchRecord[] = [];
  const allResults: MatchRecord[] = [];

  const byIsin = new Map<string, MasterSecurity>();
  const bySymbol = new Map<string, MasterSecurity>();
  const byBse = new Map<string, MasterSecurity>();
  const byNormName = new Map<string, MasterSecurity[]>();

  for (const s of masterSecurities) {
    if (s.isin) byIsin.set(s.isin.toUpperCase(), s);
    if (s.nse_symbol) bySymbol.set(s.nse_symbol.toUpperCase(), s);
    if (s.bse_code) byBse.set(String(s.bse_code), s);
    const norm = normalizeCompanyName(s.name);
    if (norm) {
      const list = byNormName.get(norm) || [];
      list.push(s);
      byNormName.set(norm, list);
    }
  }

  rows.forEach((row, idx) => {
    let rawVal = idCol && row[idCol] ? String(row[idCol]).trim() : '';
    if (!rawVal) {
      for (const col of ['isin', 'symbol', 'ticker', 'bse_code', 'name', 'company', 'Identifier']) {
        if (row[col]) {
          rawVal = String(row[col]).trim();
          break;
        }
      }
    }

    if (!rawVal) {
      const rec: MatchRecord = {
        row_index: idx,
        raw_input: row,
        status: 'unmatched',
        confidence: 0,
        notes: 'No identifier found in row',
      };
      unmatched.push(rec);
      allResults.push(rec);
      return;
    }

    const cleanUpper = rawVal.toUpperCase();

    // Tier 1: ISIN
    if (/^[A-Z]{2}[A-Z0-9]{9}[0-9]$/.test(cleanUpper) && byIsin.has(cleanUpper)) {
      const sec = byIsin.get(cleanUpper)!;
      const pnl = computeClientPnL(row, sec.close_price);
      const rec: MatchRecord = {
        row_index: idx,
        raw_input: row,
        status: 'matched',
        matched_security: sec,
        match_tier: 'isin',
        confidence: 100.0,
        notes: `Exact ISIN match: ${cleanUpper}`,
        pnl,
      };
      matched.push(rec);
      allResults.push(rec);
      return;
    }

    // Tier 2: NSE Symbol
    if (bySymbol.has(cleanUpper)) {
      const sec = bySymbol.get(cleanUpper)!;
      const pnl = computeClientPnL(row, sec.close_price);
      const rec: MatchRecord = {
        row_index: idx,
        raw_input: row,
        status: 'matched',
        matched_security: sec,
        match_tier: 'nse_symbol',
        confidence: 100.0,
        notes: `Exact NSE symbol match: ${cleanUpper}`,
        pnl,
      };
      matched.push(rec);
      allResults.push(rec);
      return;
    }

    // Tier 3: BSE Code
    if (byBse.has(rawVal)) {
      const sec = byBse.get(rawVal)!;
      const pnl = computeClientPnL(row, sec.close_price);
      const rec: MatchRecord = {
        row_index: idx,
        raw_input: row,
        status: 'matched',
        matched_security: sec,
        match_tier: 'bse_code',
        confidence: 100.0,
        notes: `Exact BSE code match: ${rawVal}`,
        pnl,
      };
      matched.push(rec);
      allResults.push(rec);
      return;
    }

    // Tier 4: Normalized Name
    const norm = normalizeCompanyName(rawVal);
    if (norm && byNormName.has(norm)) {
      const candidates = byNormName.get(norm)!;
      if (candidates.length === 1) {
        const sec = candidates[0];
        const pnl = computeClientPnL(row, sec.close_price);
        const rec: MatchRecord = {
          row_index: idx,
          raw_input: row,
          status: 'matched',
          matched_security: sec,
          match_tier: 'normalized_name',
          confidence: 98.0,
          notes: `Exact normalized name match: '${norm}'`,
          pnl,
        };
        matched.push(rec);
        allResults.push(rec);
        return;
      } else {
        const rec: MatchRecord = {
          row_index: idx,
          raw_input: row,
          status: 'ambiguous',
          match_tier: 'normalized_name',
          confidence: 95.0,
          candidates,
          notes: `Multiple securities matched company name '${rawVal}' (${candidates.length} candidates)`,
        };
        ambiguous.push(rec);
        allResults.push(rec);
        return;
      }
    }

    // Tier 5: Fuzzy / Token Match
    const tokens = new Set(norm.split(' ').filter(Boolean));
    const scored: Array<{ score: number; sec: MasterSecurity }> = [];

    for (const sec of masterSecurities) {
      const secNorm = normalizeCompanyName(sec.name);
      const secTokens = new Set(secNorm.split(' ').filter(Boolean));
      // Token overlap
      let intersection = 0;
      for (const t of tokens) {
        if (secTokens.has(t)) intersection++;
      }
      const tokenScore = tokens.size > 0 ? (intersection / tokens.size) * 100 : 0;
      if (tokenScore >= 80) {
        scored.push({ score: tokenScore, sec });
      }
    }

    scored.sort((a, b) => b.score - a.score);

    if (scored.length > 0) {
      const topScore = scored[0].score;
      const topCandidates = scored.filter((s) => topScore - s.score <= 5).map((s) => s.sec);
      if (topCandidates.length > 1) {
        const rec: MatchRecord = {
          row_index: idx,
          raw_input: row,
          status: 'ambiguous',
          match_tier: 'fuzzy_name',
          confidence: topScore,
          candidates: topCandidates,
          notes: `Ambiguous fuzzy match (${topCandidates.length} candidates with score ~${topScore}%)`,
        };
        ambiguous.push(rec);
        allResults.push(rec);
        return;
      } else {
        const sec = scored[0].sec;
        const pnl = computeClientPnL(row, sec.close_price);
        const rec: MatchRecord = {
          row_index: idx,
          raw_input: row,
          status: 'matched',
          matched_security: sec,
          match_tier: 'fuzzy_name',
          confidence: topScore,
          notes: `Fuzzy name match (score: ${topScore}%)`,
          pnl,
        };
        matched.push(rec);
        allResults.push(rec);
        return;
      }
    }

    // Unmatched
    const rec: MatchRecord = {
      row_index: idx,
      raw_input: row,
      status: 'unmatched',
      confidence: 0,
      notes: 'No matching security found in master list',
    };
    unmatched.push(rec);
    allResults.push(rec);
  });

  return {
    total_rows: rows.length,
    matched_count: matched.length,
    ambiguous_count: ambiguous.length,
    unmatched_count: unmatched.length,
    matched,
    ambiguous,
    unmatched,
    all_results: allResults,
  };
}

export function convertMatchReportToStockRows(
  report: MatchReport,
  resolvedAmbiguous: Record<number, MasterSecurity> = {},
  manualMatches: Record<number, MasterSecurity> = {}
): StockRow[] {
  const rows: StockRow[] = [];

  // 1. Matched rows
  for (const m of report.matched) {
    const sec = m.matched_security!;
    const v: Record<string, number | null> = {
      market_cap: sec.market_cap,
      close_price: sec.close_price,
      pe_ratio: sec.pe_ratio ?? null,
      return_on_equity: sec.return_on_equity ?? null,
    };
    if (m.pnl?.quantity !== undefined && m.pnl?.quantity !== null) {
      v['quantity'] = m.pnl.quantity;
      v['buy_price'] = m.pnl.buy_price ?? null;
      v['invested_value'] = m.pnl.invested_value ?? null;
      v['current_value'] = m.pnl.current_value ?? null;
      v['pnl_amount'] = m.pnl.pnl_amount ?? null;
      v['pnl_pct'] = m.pnl.pnl_pct ?? null;
    }
    rows.push({
      name: sec.name,
      sub: sec.sub_sector,
      sector: sec.sector,
      v,
    });
  }

  // 2. Ambiguous rows resolved by user
  for (const amb of report.ambiguous) {
    const chosen = resolvedAmbiguous[amb.row_index];
    if (chosen) {
      const pnl = computeClientPnL(amb.raw_input, chosen.close_price);
      const v: Record<string, number | null> = {
        market_cap: chosen.market_cap,
        close_price: chosen.close_price,
        pe_ratio: chosen.pe_ratio ?? null,
        return_on_equity: chosen.return_on_equity ?? null,
      };
      if (pnl.quantity !== undefined && pnl.quantity !== null) {
        v['quantity'] = pnl.quantity;
        v['buy_price'] = pnl.buy_price ?? null;
        v['invested_value'] = pnl.invested_value ?? null;
        v['current_value'] = pnl.current_value ?? null;
        v['pnl_amount'] = pnl.pnl_amount ?? null;
        v['pnl_pct'] = pnl.pnl_pct ?? null;
      }
      rows.push({
        name: chosen.name,
        sub: chosen.sub_sector,
        sector: chosen.sector,
        v,
      });
    }
  }

  // 3. Unmatched rows manually matched by user
  for (const unm of report.unmatched) {
    const chosen = manualMatches[unm.row_index];
    if (chosen) {
      const pnl = computeClientPnL(unm.raw_input, chosen.close_price);
      const v: Record<string, number | null> = {
        market_cap: chosen.market_cap,
        close_price: chosen.close_price,
        pe_ratio: chosen.pe_ratio ?? null,
        return_on_equity: chosen.return_on_equity ?? null,
      };
      if (pnl.quantity !== undefined && pnl.quantity !== null) {
        v['quantity'] = pnl.quantity;
        v['buy_price'] = pnl.buy_price ?? null;
        v['invested_value'] = pnl.invested_value ?? null;
        v['current_value'] = pnl.current_value ?? null;
        v['pnl_amount'] = pnl.pnl_amount ?? null;
        v['pnl_pct'] = pnl.pnl_pct ?? null;
      }
      rows.push({
        name: chosen.name,
        sub: chosen.sub_sector,
        sector: chosen.sector,
        v,
      });
    }
  }

  return rows;
}
