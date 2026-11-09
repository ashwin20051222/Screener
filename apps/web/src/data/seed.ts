import { StockRow } from '../types';

export const SEED_ROWS_RAW: StockRow[] = [
  {
    name: 'Reliance Industries Ltd',
    sub: 'Oil & Gas - Refining & Marketing',
    sector: 'Energy',
    v: {
      market_cap: 1639061.09,
      close_price: 1202.00,
      pe_ratio: 20.29,
      '1m_return': -2.60,
      '1d_return': -0.76,
      return_on_equity: 7.71,
    },
  },
  {
    name: 'Bharti Airtel Ltd',
    sub: 'Telecom Services',
    sector: 'Communication Services',
    v: {
      market_cap: 1188457.35,
      close_price: 1875.20,
      pe_ratio: 44.52,
      '1m_return': 1.31,
      '1d_return': -1.56,
      return_on_equity: 15.28,
    },
  },
  {
    name: 'HDFC Bank Limited',
    sub: 'Private Banks',
    sector: 'Financials',
    v: {
      market_cap: 1123775.87,
      close_price: 712.00,
      pe_ratio: 14.78,
      '1m_return': -2.60,
      '1d_return': -2.31,
      return_on_equity: 13.26,
    },
  },
  {
    name: 'ICICI Bank Limited',
    sub: 'Private Banks',
    sector: 'Financials',
    v: {
      market_cap: 1003030.89,
      close_price: 1381.00,
      pe_ratio: 18.50,
      '1m_return': 2.46,
      '1d_return': -1.15,
      return_on_equity: 15.31,
    },
  },
  {
    name: 'Tata Consultancy Services Ltd',
    sub: 'IT Services & Consulting',
    sector: 'Information Technology',
    v: {
      market_cap: 891858.57,
      close_price: 2460.90,
      pe_ratio: 18.12,
      '1m_return': 17.75,
      '1d_return': -0.17,
      return_on_equity: 48.19,
    },
  },
  {
    name: 'State Bank of India',
    sub: 'Public Banks',
    sector: 'Financials',
    v: {
      market_cap: 888553.61,
      close_price: 973.70,
      pe_ratio: 10.67,
      '1m_return': -1.82,
      '1d_return': 1.15,
      return_on_equity: 14.88,
    },
  },
  {
    name: 'Bajaj Finance Ltd',
    sub: 'Consumer Finance',
    sector: 'Financials',
    v: {
      market_cap: 611249.60,
      close_price: 957.35,
      pe_ratio: 32.14,
      '1m_return': -7.50,
      '1d_return': -2.52,
      return_on_equity: 17.62,
    },
  },
  {
    name: 'Life Insurance Corporation Of India',
    sub: 'Insurance',
    sector: 'Financials',
    v: {
      market_cap: 503153.57,
      close_price: 393.35,
      pe_ratio: 8.76,
      '1m_return': -1.71,
      '1d_return': -1.11,
      return_on_equity: 37.75,
    },
  },
  {
    name: 'Larsen and Toubro Ltd',
    sub: 'Construction & Engineering',
    sector: 'Industrials',
    v: {
      market_cap: 499050.87,
      close_price: 3661.90,
      pe_ratio: 31.03,
      '1m_return': -5.74,
      '1d_return': 0.96,
      return_on_equity: 13.19,
    },
  },
  {
    name: 'Infosys Limited',
    sub: 'IT Services & Consulting',
    sector: 'Information Technology',
    v: {
      market_cap: 470325.89,
      close_price: 1130.70,
      pe_ratio: 15.98,
      '1m_return': 8.56,
      '1d_return': -2.63,
      return_on_equity: 31.07,
    },
  },
  {
    name: 'Kotak Mahindra Bank Ltd',
    sub: 'Private Banks',
    sector: 'Financials',
    v: {
      market_cap: 445068.21,
      close_price: 442.30,
      pe_ratio: 23.08,
      '1m_return': 6.53,
      '1d_return': -1.14,
      return_on_equity: 11.39,
    },
  },
  {
    name: 'Hindustan Unilever Ltd',
    sub: 'FMCG - Household Products',
    sector: 'Consumer Staples',
    v: {
      market_cap: 444965.59,
      close_price: 1853.20,
      pe_ratio: 29.59,
      '1m_return': -4.47,
      '1d_return': -2.14,
      return_on_equity: 30.50,
    },
  },
  {
    name: 'National Stock Exchange of India Ltd',
    sub: 'Stock Exchanges & Ratings',
    sector: 'Financials',
    v: {
      market_cap: 432988.88,
      close_price: 1726.55,
      pe_ratio: 42.03,
      '1m_return': -4.12,
      '1d_return': -1.31,
      return_on_equity: 32.98,
    },
  },
  {
    name: 'Sun Pharmaceutical Industries Ltd',
    sub: 'Pharmaceuticals',
    sector: 'Health Care',
    v: {
      market_cap: 421995.03,
      close_price: 1743.00,
      pe_ratio: 36.76,
      '1m_return': -4.87,
      '1d_return': -0.90,
      return_on_equity: 14.68,
    },
  },
  {
    name: 'Adani Ports and Special Economic Zone Ltd',
    sub: 'Ports',
    sector: 'Industrials',
    v: {
      market_cap: 403377.16,
      close_price: 1766.00,
      pe_ratio: 31.50,
      '1m_return': -1.54,
      '1d_return': 0.87,
      return_on_equity: 15.59,
    },
  },
];

// Helper to calculate median of non-null positive numbers
export const median = (nums: (number | null)[]): number | null => {
  const filtered = nums.filter((x): x is number => x !== null && x > 0).sort((a, b) => a - b);
  if (!filtered.length) return null;
  return filtered[Math.floor(filtered.length / 2)];
};

// Sector hierarchy with sub-sectors from seed + market classifications
export const SECTORS_CONFIG: Record<string, { count: number; subSectors: Record<string, number> }> = {
  'Consumer Discretionary': {
    count: 24,
    subSectors: {
      'Auto Components': 8,
      'Automobiles': 6,
      'Consumer Electronics': 4,
      'Footwear': 3,
      'Hotels & Restaurants': 3,
    },
  },
  'Communication Services': {
    count: 11,
    subSectors: {
      'Telecom Services': 4,
      'Media & Entertainment': 5,
      'Advertising': 2,
    },
  },
  'Consumer Staples': {
    count: 12,
    subSectors: {
      'FMCG - Household Products': 5,
      'Packaged Foods': 4,
      'Agricultural Products': 3,
    },
  },
  'Energy': {
    count: 4,
    subSectors: {
      'Oil & Gas - Refining & Marketing': 2,
      'Oil Exploration': 1,
      'Renewable Energy': 1,
    },
  },
  'Financials': {
    count: 12,
    subSectors: {
      'Private Banks': 4,
      'Public Banks': 2,
      'Consumer Finance': 3,
      'Insurance': 2,
      'Stock Exchanges & Ratings': 1,
    },
  },
  'Health Care': {
    count: 5,
    subSectors: {
      'Pharmaceuticals': 3,
      'Hospitals & Healthcare Services': 1,
      'Biotechnology': 1,
    },
  },
  'Industrials': {
    count: 37,
    subSectors: {
      'Construction & Engineering': 12,
      'Ports': 4,
      'Industrial Machinery': 10,
      'Aerospace & Defense': 6,
      'Transportation': 5,
    },
  },
  'Information Technology': {
    count: 7,
    subSectors: {
      'IT Services & Consulting': 5,
      'Software Products': 2,
    },
  },
  'Materials': {
    count: 24,
    subSectors: {
      'Iron & Steel': 8,
      'Specialty Chemicals': 7,
      'Cement': 5,
      'Metals & Mining': 4,
    },
  },
  'Real Estate': {
    count: 2,
    subSectors: {
      'Residential & Commercial Developers': 2,
    },
  },
  'Utilities': {
    count: 7,
    subSectors: {
      'Power Generation': 4,
      'Power Distribution': 3,
    },
  },
  'ETF': {
    count: 4,
    subSectors: {
      'Equity ETF': 2,
      'Debt ETF': 1,
      'Commodity ETF': 1,
    },
  },
};

// Derive relative and benchmark metrics
export function deriveMetrics(rows: StockRow[]): StockRow[] {
  const deepCloned: StockRow[] = JSON.parse(JSON.stringify(rows));
  
  const metricConfigs: [string, string, string?][] = [
    ['pe_ratio', 'pe_premium_vs_', 'sector_pe'],
    ['pb_ratio', 'pb_premium_vs_', 'sector_pb'],
    ['ps_ratio', 'ps_premium_vs_'],
    ['dividend_yield', 'dividend_yield_vs_', 'sector_dividend_yield'],
  ];

  metricConfigs.forEach(([metric, prefix, sectorBenchmarkKey]) => {
    (['sector', 'sub'] as const).forEach(groupKey => {
      const groups: Record<string, (number | null)[]> = {};
      deepCloned.forEach(r => {
        const key = r[groupKey];
        if (!groups[key]) groups[key] = [];
        groups[key].push(r.v[metric] ?? null);
      });

      deepCloned.forEach(r => {
        const key = r[groupKey];
        const groupVals = groups[key] || [];
        const bench = median(groupVals);
        const val = r.v[metric];
        
        if (bench !== null && val !== null && val !== undefined && groupVals.filter(y => y !== null).length > 1) {
          const isDivYield = metric === 'dividend_yield';
          const targetKey = prefix + (groupKey === 'sub' ? 'sub_sector' : 'sector');
          r.v[targetKey] = isDivYield ? val - bench : ((val / bench) - 1) * 100;
          if (sectorBenchmarkKey && groupKey === 'sector') {
            r.v[sectorBenchmarkKey] = bench;
          }
        }
      });
    });
  });

  return deepCloned;
}

export const INITIAL_SEED_ROWS = deriveMetrics(SEED_ROWS_RAW);
