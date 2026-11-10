export type AvailabilityStatus = 
  | 'Official-direct'
  | 'Computed-from-official'
  | 'Approximate'
  | 'Unavailable';

export interface FilterDefinition {
  id: string;
  name: string;
  category: string;
  unit: string;
  in_screenshot: boolean;
  locked_in_original: boolean;
  needs_official_source: boolean;
  availability: AvailabilityStatus;
  feeds?: string;
  formula?: string;
  frequency?: string;
  null_rule?: string;
  direction_of_goodness?: string;
  glossary?: string;
}

export interface UniverseMeta {
  id: string;
  label: string;
  slug: string;
  count: number;
  as_of: string | null;
}

export interface FilterState {
  id: string;
  min: number | null;
  max: number | null;
}

export interface StockRow {
  name: string;
  sub: string;
  sector: string;
  nse_symbol?: string;
  _provenance?: Record<string, any>;
  v: Record<string, number | null>;
}

export interface StockUniverse {
  id: string;
  name: string;
  type: 'default' | 'custom';
  rows: StockRow[];
}

export interface SavedScreen {
  id: string;
  name: string;
  note: string;
  filters: FilterState[];
  columns: string[];
  sort: { id: string; dir: 1 | -1 };
  createdAt: string;
}

export interface CustomFilter {
  id: string;
  name: string;
  formula: string;
  fn: (r: StockRow) => number | null;
}

export type MatchStatus = 'matched' | 'ambiguous' | 'unmatched';

export interface PnLData {
  quantity?: number | null;
  buy_price?: number | null;
  invested_value?: number | null;
  current_value?: number | null;
  pnl_amount?: number | null;
  pnl_pct?: number | null;
}

export interface MatchRecord {
  row_index: number;
  raw_input: Record<string, any>;
  status: MatchStatus;
  matched_security?: Record<string, any> | null;
  match_tier?: string | null;
  confidence: number;
  candidates?: Array<Record<string, any>>;
  notes?: string;
  pnl?: PnLData;
}

export interface MatchReport {
  total_rows: number;
  matched_count: number;
  ambiguous_count: number;
  unmatched_count: number;
  matched: MatchRecord[];
  ambiguous: MatchRecord[];
  unmatched: MatchRecord[];
  all_results: MatchRecord[];
}
