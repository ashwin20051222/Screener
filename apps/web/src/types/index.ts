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
  formula?: string;
  frequency?: string;
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
  v: Record<string, number | null>;
}

export interface StockUniverse {
  id: string;
  name: string;
  type: 'default' | 'custom';
  rows: StockRow[];
  totalMarketCount?: number;
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
