import React, { useState, useMemo, useEffect, useRef } from 'react';
import filtersData from './data/filters.json';
import {
  FilterDefinition,
  FilterState,
  StockRow,
  StockUniverse,
  SavedScreen,
  UniverseMeta,
} from './types';
import {
  INITIAL_SEED_ROWS,
  SECTORS_CONFIG,
  deriveMetrics,
} from './data/seed';
import { NumericFilterWidget } from './components/NumericFilterWidget';
import { AddFiltersModal, FilterCoverageStats, formatMissingFeedReason } from './components/AddFiltersModal';
import { GlossaryModal } from './components/GlossaryModal';
import { CustomFilterModal } from './components/CustomFilterModal';
import { StockDetailDrawer } from './components/StockDetailDrawer';
import { SavedScreensModal } from './components/SavedScreensModal';
import { ColumnPicker } from './components/ColumnPicker';
import { ExportMenu } from './components/ExportMenu';
import { ExcelUploadModal } from './components/ExcelUploadModal';
import { MatchReportModal } from './components/MatchReportModal';
import { exportTableData } from './utils/export';
import { formatIndianNumber } from './utils/formatters';
import { ParsedWorkbookInfo } from './utils/excelParser';
import {
  CLIENT_MASTER_SECURITIES,
  matchUniverseClient,
} from './utils/matcherClient';
import { MatchReport } from './types';
import {
  Search,
  ChevronDown,
  ChevronUp,
  Share2,
  Pencil,
  Clock,
  HelpCircle,
  Plus,
  ArrowDown,
  ArrowUp,
  Sun,
  Moon,
  Trash2,
} from 'lucide-react';
import * as XLSX from 'xlsx';

// Load filter definitions
const ALL_FILTERS_MAP = new Map<string, FilterDefinition>(
  Object.entries(filtersData.filters).map(([k, v]) => [k, v as FilterDefinition])
);

// Register portfolio custom columns for user spreadsheets
const PORTFOLIO_COLUMNS: FilterDefinition[] = [
  { id: 'quantity', name: 'Quantity', category: 'Portfolio', unit: 'shares', in_screenshot: false, locked_in_original: false, needs_official_source: false, availability: 'Computed-from-official' },
  { id: 'buy_price', name: 'Buy Price', category: 'Portfolio', unit: '₹', in_screenshot: false, locked_in_original: false, needs_official_source: false, availability: 'Computed-from-official' },
  { id: 'invested_value', name: 'Invested Value', category: 'Portfolio', unit: '₹', in_screenshot: false, locked_in_original: false, needs_official_source: false, availability: 'Computed-from-official' },
  { id: 'current_value', name: 'Current Value', category: 'Portfolio', unit: '₹', in_screenshot: false, locked_in_original: false, needs_official_source: false, availability: 'Computed-from-official' },
  { id: 'pnl_amount', name: 'P&L (₹)', category: 'Portfolio', unit: '₹', in_screenshot: false, locked_in_original: false, needs_official_source: false, availability: 'Computed-from-official' },
  { id: 'pnl_pct', name: 'P&L (%)', category: 'Portfolio', unit: '%', in_screenshot: false, locked_in_original: false, needs_official_source: false, availability: 'Computed-from-official' },
];

for (const col of PORTFOLIO_COLUMNS) {
  ALL_FILTERS_MAP.set(col.id, col);
}

const ALL_FILTERS_LIST = Array.from(ALL_FILTERS_MAP.values());

// Default filters shown in left panel
const DEFAULT_FILTER_IDS = [
  'market_cap',
  'close_price',
  'pe_ratio',
  '1m_return',
  '1d_return',
  'return_on_equity',
  'pb_ratio',
];

// Default columns in table (matches Screenshot 1)
const DEFAULT_COLUMNS = [
  'market_cap',
  'pe_ratio',
  '1m_return',
  '1d_return',
  'return_on_equity',
];

const FALLBACK_INDEX_UNIVERSES: UniverseMeta[] = [
  { id: 'nifty50', label: 'Nifty 50', slug: 'NIFTY50', count: 0, as_of: null },
  { id: 'niftynext50', label: 'Nifty Next 50', slug: 'NIFTYNEXT50', count: 0, as_of: null },
  { id: 'nifty100', label: 'Nifty 100', slug: 'NIFTY100', count: 0, as_of: null },
  { id: 'nifty200', label: 'Nifty 200', slug: 'NIFTY200', count: 0, as_of: null },
  { id: 'nifty500', label: 'Nifty 500', slug: 'NIFTY500', count: 0, as_of: null },
  { id: 'niftymidcap100', label: 'Nifty Midcap 100', slug: 'NIFTYMIDCAP100', count: 0, as_of: null },
  { id: 'niftymidcap150', label: 'Nifty Midcap 150', slug: 'NIFTYMIDCAP150', count: 0, as_of: null },
  { id: 'niftysmallcap100', label: 'Nifty Smallcap 100', slug: 'NIFTYSMALLCAP100', count: 0, as_of: null },
  { id: 'niftysmallcap250', label: 'Nifty Smallcap 250', slug: 'NIFTYSMALLCAP250', count: 0, as_of: null },
];

const BANK_INSURER_INAPPLICABLE_IDS = new Set([
  'cost_of_goods_sold',
  'current_ratio',
  'quick_ratio',
  'debt_to_equity',
  'long_term_debt_to_equity',
  'interest_coverage_ratio',
  'cash_conversion_cycle',
  'inventory_turnover_ratio',
  'days_of_inventory_outstanding',
  'days_payable_outstanding',
  'working_capital_turnover_ratio',
  'total_inventory',
  'accounts_payable',
]);

const CANONICAL_SECTOR_ORDER = Object.keys(SECTORS_CONFIG);

export const App: React.FC = () => {
  // Theme state
  const [theme, setTheme] = useState<'light' | 'dark'>('light');

  // Stock Universes & Live Backend State
  const [isSynced, setIsSynced] = useState(false);
  const [liveRows, setLiveRows] = useState<StockRow[]>([]);
  const [indexUniverses, setIndexUniverses] = useState<UniverseMeta[]>(FALLBACK_INDEX_UNIVERSES);
  const [allListedMeta, setAllListedMeta] = useState<UniverseMeta | null>(null);
  const [universeMembers, setUniverseMembers] = useState<Record<string, string[]>>({});
  const [selectedIndexSlugs, setSelectedIndexSlugs] = useState<Set<string>>(new Set());

  const [universes, setUniverses] = useState<StockUniverse[]>([]);
  const [activeUniverseTab, setActiveUniverseTab] = useState<'default' | 'custom'>('default');
  const [selectedUniverseIds, setSelectedUniverseIds] = useState<Set<string>>(new Set());

  // Multi-universe active rows:
  // - If no index AND no custom universe checked => entire listed market (when synced) or sample 15 rows (offline seed)
  // - If one or more checked => deduplicated union across selected index constituents & custom Excel universes
  const activeRows = useMemo(() => {
    const baseRows = isSynced ? liveRows : INITIAL_SEED_ROWS;
    const selectedCustom = universes.filter((u) => u.type === 'custom' && selectedUniverseIds.has(u.id));
    if (selectedIndexSlugs.size === 0 && selectedCustom.length === 0) {
      return baseRows;
    }

    const allowedSymbols = new Set<string>();
    for (const slug of selectedIndexSlugs) {
      for (const sym of (universeMembers[slug] || [])) {
        allowedSymbols.add(sym);
      }
    }

    const seen = new Set<string>();
    const unionRows: StockRow[] = [];
    if (selectedIndexSlugs.size > 0) {
      for (const r of baseRows) {
        const key = r.nse_symbol || r.name;
        if (r.nse_symbol && allowedSymbols.has(r.nse_symbol) && !seen.has(key)) {
          seen.add(key);
          unionRows.push(r);
        }
      }
    }
    for (const u of selectedCustom) {
      for (const r of u.rows) {
        const key = r.nse_symbol || r.name;
        if (!seen.has(key)) {
          seen.add(key);
          unionRows.push(r);
        }
      }
    }
    return unionRows;
  }, [isSynced, liveRows, universes, selectedUniverseIds, selectedIndexSlugs, universeMembers]);

  const [showMoreUniverses, setShowMoreUniverses] = useState(false);

  const handleProceedToMatch = (parsed: ParsedWorkbookInfo, selectedIdCol: string) => {
    setIsExcelUploadOpen(false);
    setUploadedFilename(parsed.selectedSheet || 'My Uploaded Universe');
    const report = matchUniverseClient(parsed.rows, selectedIdCol);
    setMatchReportData(report);
    setIsMatchReportOpen(true);
  };

  const handleSaveCustomUniverse = (newUniverse: StockUniverse) => {
    setUniverses((prev) => [...prev, newUniverse]);
    setSelectedUniverseIds((prev) => new Set([...prev, newUniverse.id]));
    setActiveUniverseTab('custom');

    // Auto-enable custom portfolio columns if available
    const hasPnl = newUniverse.rows.some(
      (r) => r.v.quantity !== undefined && r.v.quantity !== null
    );
    if (hasPnl) {
      setColumns((prev) => {
        const next = [...prev];
        if (!next.includes('quantity')) next.push('quantity');
        if (!next.includes('buy_price')) next.push('buy_price');
        if (!next.includes('pnl_amount')) next.push('pnl_amount');
        if (!next.includes('pnl_pct')) next.push('pnl_pct');
        return next;
      });
    }
  };

  const toggleIndexSelection = (slug: string) => {
    setSelectedIndexSlugs((prev) => {
      const next = new Set(prev);
      if (next.has(slug)) next.delete(slug);
      else next.add(slug);
      return next;
    });
    setVisibleLimit(20);
  };

  const toggleUniverseSelection = (id: string) => {
    setSelectedUniverseIds((prev) => {
      const next = new Set(prev);
      if (next.has(id)) next.delete(id);
      else next.add(id);
      return next;
    });
    setVisibleLimit(20);
  };

  const handleDeleteUniverse = (id: string) => {
    setUniverses((prev) => prev.filter((u) => u.id !== id));
    setSelectedUniverseIds((prev) => {
      const next = new Set(prev);
      next.delete(id);
      return next;
    });
  };

  const handleRenameUniverse = (id: string, currentName: string) => {
    const newName = window.prompt('Rename universe:', currentName);
    if (newName && newName.trim()) {
      setUniverses((prev) =>
        prev.map((u) => (u.id === id ? { ...u, name: newName.trim() } : u))
      );
    }
  };

  // Sector filtering
  const [sectorSearch, setSectorSearch] = useState('');
  const [selectedSectors, setSelectedSectors] = useState<Set<string>>(new Set());
  const [selectedSubSectors, setSelectedSubSectors] = useState<Set<string>>(new Set());
  const [expandedSectors, setExpandedSectors] = useState<Set<string>>(new Set());

  // Filter States
  const [filters, setFilters] = useState<FilterState[]>(
    DEFAULT_FILTER_IDS.map(id => ({ id, min: null, max: null }))
  );
  // Default open sections matching Screenshot 1: Stock Universe and Sector only
  const [openSections, setOpenSections] = useState<Set<string>>(
    new Set(['stock_universe', 'sector'])
  );

  // Columns & Sorting
  const [columns, setColumns] = useState<string[]>(DEFAULT_COLUMNS);
  const [sort, setSort] = useState<{ id: string; dir: 1 | -1 }>({
    id: 'market_cap',
    dir: -1,
  });

  // Note & Saved Screens & Infinite Scroll
  const [note, setNote] = useState('');
  const [savedScreens, setSavedScreens] = useState<SavedScreen[]>([]);
  const [isDirty, setIsDirty] = useState(false);
  const [selectedStock, setSelectedStock] = useState<StockRow | null>(null);
  const [visibleLimit, setVisibleLimit] = useState(20);
  const [liveSyncSourceLabel, setLiveSyncSourceLabel] = useState<string | null>(null);

  // Synchronous initialization from URL params for Visual QA
  const getInitialParam = (k: string) => {
    try {
      return new URLSearchParams(window.location.search).get(k);
    } catch {
      return null;
    }
  };

  // Hydrate universes and live dataset from FastAPI + DuckDB backend
  useEffect(() => {
    let cancelled = false;
    Promise.all([
      fetch('/api/universes').then((r) => (r.ok ? r.json() : null)).catch(() => null),
      fetch('/api/screener/dataset').then((r) => (r.ok ? r.json() : null)).catch(() => null),
    ]).then(([uData, dData]) => {
      if (cancelled) return;
      if (Array.isArray(uData) && uData.length > 0) {
        const allEntry = uData.find((u: UniverseMeta) => u.slug === 'ALL') || null;
        const indices = uData.filter((u: UniverseMeta) => u.slug !== 'ALL');
        setIndexUniverses(indices.length > 0 ? indices : FALLBACK_INDEX_UNIVERSES);
        setAllListedMeta(allEntry);
      }
      if (dData && dData.synced && Array.isArray(dData.rows) && dData.rows.length > 0) {
        const parsedLiveRows: StockRow[] = dData.rows.map((r: Record<string, any>) => ({
          name: r.name || r.nse_symbol || 'Unknown',
          sub: r.sub_sector || 'Unclassified',
          sector: r.sector || 'Unclassified',
          nse_symbol: r.nse_symbol || undefined,
          _provenance: r._provenance || undefined,
          v: Object.fromEntries(
            Object.entries(r).filter(([k, val]) => !k.startsWith('_') && (typeof val === 'number' || val === null))
          ) as Record<string, number | null>,
        }));
        setLiveRows(parsedLiveRows);
        setUniverseMembers(dData.universes || {});
        setIsSynced(true);
        const asOf = dData.as_of || {};
        const parts = [
          asOf.price ? `Price: ${asOf.price}` : null,
          asOf.masters ? `Masters: ${asOf.masters}` : null,
          asOf.filings ? `Filings: ${asOf.filings}` : null,
          asOf.amfi ? `AMFI: ${asOf.amfi}` : null,
        ].filter(Boolean);
        setLiveSyncSourceLabel(
          `Official DuckDB (${parsedLiveRows.length} stocks)${parts.length ? ' · ' + parts.join(' · ') : ''}`
        );
      }
    });
    return () => {
      cancelled = true;
    };
  }, []);

  const initialModalParam = getInitialParam('modal');
  const catLookup: Record<string, string> = {
    profitability: 'Profitability',
    growth: 'Growth',
    valuation: 'Valuation',
    ownership: 'Ownership',
    fno: 'Futures & Options',
    price_volume: 'Price and Volume',
    financial_ratios: 'Financial Ratios',
    special: 'Special',
    analyst_ratings: 'Analyst Ratings',
    technical_indicators: 'Technical Indicators',
    balance_sheet: 'Balance Sheet & Cash Flow',
    etfs: 'ETFs',
    income_statement: 'Income Statement',
    your_filters: 'Your Filters',
  };

  // Modals
  const [isAddFilterModalOpen, setIsAddFilterModalOpen] = useState(!!initialModalParam);
  const [modalCategory, setModalCategory] = useState<string>(
    (initialModalParam && catLookup[initialModalParam.toLowerCase()]) || 'Profitability'
  );
  const [isGlossaryModalOpen, setIsGlossaryModalOpen] = useState(!!getInitialParam('glossary'));
  const [glossaryCategory, setGlossaryCategory] = useState(getInitialParam('glossary') || 'Profitability');
  const [isCustomFilterModalOpen, setIsCustomFilterModalOpen] = useState(false);
  const [isSavedScreensModalOpen, setIsSavedScreensModalOpen] = useState(false);
  const [isColumnPickerOpen, setIsColumnPickerOpen] = useState(false);
  const [isExportMenuOpen, setIsExportMenuOpen] = useState(false);
  const [toastMessage, setToastMessage] = useState<string | null>(null);

  // Excel & Universe modals
  const isUploadParam = !!getInitialParam('upload');
  const isMatchReportParam = !!getInitialParam('matchreport');

  const [isExcelUploadOpen, setIsExcelUploadOpen] = useState(isUploadParam);
  const [isMatchReportOpen, setIsMatchReportOpen] = useState(isMatchReportParam);
  const [matchReportData, setMatchReportData] = useState<MatchReport | null>(() => {
    if (isMatchReportParam) {
      const sample30 = [
        { Identifier: 'INE002A01018', Quantity: 50, Buy_Price: 2200, Notes: 'Core holding' },
        { Identifier: 'TCS', Quantity: 30, Buy_Price: 3200, Notes: 'IT bellwether' },
        { Identifier: 'INE040A01034', Quantity: 100, Buy_Price: 1500, Notes: 'Banking leader' },
        { Identifier: 'ICICIBANK', Quantity: 120, Buy_Price: 850, Notes: 'Private bank' },
        { Identifier: 'INE009A01021', Quantity: 80, Buy_Price: 1350, Notes: 'IT export' },
        { Identifier: 'HINDUNILVR', Quantity: 40, Buy_Price: 2400, Notes: 'FMCG staple' },
        { Identifier: '500875', Quantity: 200, Buy_Price: 380, Notes: 'High dividend' },
        { Identifier: 'SBIN', Quantity: 150, Buy_Price: 520, Notes: 'PSU bank' },
        { Identifier: 'BHARTIARTL', Quantity: 90, Buy_Price: 780, Notes: 'Telecom' },
        { Identifier: 'BAJFINANCE', Quantity: 15, Buy_Price: 6200, Notes: 'NBFC lending' },
        { Identifier: '500820', Quantity: 25, Buy_Price: 2900, Notes: 'Decorative paints' },
        { Identifier: 'MARUTI', Quantity: 10, Buy_Price: 8800, Notes: 'Auto 4-wheeler' },
        { Identifier: 'INE280A01028', Quantity: 35, Buy_Price: 2700, Notes: 'Jewellery retail' },
        { Identifier: 'SUNPHARMA', Quantity: 60, Buy_Price: 980, Notes: 'Pharma generic' },
        { Identifier: 'Tata Steel Limited', Quantity: 300, Buy_Price: 115, Notes: 'Metals & mining' },
        { Identifier: 'AXISBANK', Quantity: 70, Buy_Price: 910, Notes: 'Private bank' },
        { Identifier: 'Wipro Limited', Quantity: 110, Buy_Price: 390, Notes: 'IT services' },
        { Identifier: 'HCL Technologies Limited', Quantity: 45, Buy_Price: 1100, Notes: 'IT dividend' },
        { Identifier: '500103', Quantity: 250, Buy_Price: 85, Notes: 'Capital goods' },
        { Identifier: 'POWERGRID', Quantity: 180, Buy_Price: 190, Notes: 'Power transmission' },
        { Identifier: 'NTPC Limited', Quantity: 220, Buy_Price: 180, Notes: 'Power generation' },
        { Identifier: 'INF204KB14I2', Quantity: 500, Buy_Price: 220, Notes: 'Nifty 50 ETF' },
        { Identifier: 'GOLDBEES', Quantity: 800, Buy_Price: 50, Notes: 'Gold ETF' },
        { Identifier: '540115', Quantity: 12, Buy_Price: 4500, Notes: 'ER&D IT' },
        { Identifier: 'INF204KB17I5', Quantity: 400, Buy_Price: 52, Notes: 'Commodity gold' },
        { Identifier: 'Tata Motors', Quantity: 100, Buy_Price: 550, Notes: 'Ambiguous' },
        { Identifier: 'L&T', Quantity: 20, Buy_Price: 2800, Notes: 'Ambiguous' },
        { Identifier: 'Acme Quantum Robotics Ltd', Quantity: 100, Buy_Price: 100, Notes: 'Unmatched' },
        { Identifier: 'INE999Z99999', Quantity: 50, Buy_Price: 250, Notes: 'Unmatched' },
        { Identifier: 'Atlantis Global Trading', Quantity: 75, Buy_Price: 50, Notes: 'Unmatched' },
      ];
      return matchUniverseClient(sample30, 'Identifier');
    }
    return null;
  });
  const [uploadedFilename, setUploadedFilename] = useState('My Uploaded Portfolio');

  const fileInputRef = useRef<HTMLInputElement>(null);


  // URL parameter support for Visual QA state reproduction
  useEffect(() => {
    const params = new URLSearchParams(window.location.search);
    const stateParam = params.get('state');
    const modalParam = params.get('modal');
    const glossaryParam = params.get('glossary');
    const drawerParam = params.get('drawer');

    if (stateParam === '2') {
      // Screenshot 2: Market Cap & Close Price expanded, Close Price column added
      setOpenSections(new Set(['f_market_cap', 'f_close_price']));
      setColumns(['market_cap', 'close_price', 'pe_ratio', '1m_return', '1d_return', 'return_on_equity']);
    } else if (stateParam === '3') {
      // Screenshot 3: PE, 1M Return, 1D Return expanded
      setOpenSections(new Set(['f_pe_ratio', 'f_1m_return', 'f_1d_return']));
      setColumns(['market_cap', 'close_price', 'pe_ratio', '1m_return', '1d_return', 'return_on_equity']);
    } else if (stateParam === '4') {
      // Screenshot 4: Return on Equity & PB Ratio expanded
      setOpenSections(new Set(['f_return_on_equity', 'f_pb_ratio']));
      setColumns(['market_cap', 'close_price', 'pe_ratio', '1m_return', '1d_return', 'return_on_equity']);
    }

    if (modalParam) {
      setIsAddFilterModalOpen(true);
      const catMap: Record<string, string> = {
        profitability: 'Profitability',
        growth: 'Growth',
        valuation: 'Valuation',
        ownership: 'Ownership',
        fno: 'Futures & Options',
        price_volume: 'Price and Volume',
        financial_ratios: 'Financial Ratios',
        special: 'Special',
        analyst_ratings: 'Analyst Ratings',
        technical_indicators: 'Technical Indicators',
        balance_sheet: 'Balance Sheet & Cash Flow',
        etfs: 'ETFs',
        income_statement: 'Income Statement',
        your_filters: 'Your Filters',
      };
      if (catMap[modalParam.toLowerCase()]) {
        setModalCategory(catMap[modalParam.toLowerCase()]);
      }
    }

    if (glossaryParam) {
      setGlossaryCategory(glossaryParam);
      setIsGlossaryModalOpen(true);
    }

    if (drawerParam) {
      setSelectedStock(activeRows[0]);
    }
  }, [activeRows]);

  const showToast = (msg: string) => {
    setToastMessage(msg);
    setTimeout(() => setToastMessage(null), 3000);
  };

  // Toggle theme
  const toggleTheme = () => {
    const nextTheme = theme === 'light' ? 'dark' : 'light';
    setTheme(nextTheme);
    document.documentElement.setAttribute('data-theme', nextTheme);
  };


  // Set of loaded metric IDs + exact per-filter coverage over activeRows
  const { loadedFilterIds, filterCoverage } = useMemo(() => {
    const ids = new Set<string>();
    const counts = new Map<string, number>();
    const total = activeRows.length;
    activeRows.forEach(r => {
      Object.entries(r.v).forEach(([k, val]) => {
        if (val !== null && val !== undefined) {
          ids.add(k);
          counts.set(k, (counts.get(k) || 0) + 1);
        }
      });
    });
    const covMap = new Map<string, FilterCoverageStats>();
    ALL_FILTERS_LIST.forEach(f => {
      const nonNull = counts.get(f.id) || 0;
      covMap.set(f.id, {
        nonNull,
        total,
        pct: total > 0 ? (nonNull / total) * 100 : 0,
      });
    });
    return { loadedFilterIds: ids, filterCoverage: covMap };
  }, [activeRows]);

  // Dynamic sector & sub-sector counts computed strictly from activeRows (before sector filters)
  const dynamicSectorsMap = useMemo(() => {
    const map = new Map<string, { count: number; subSectors: Map<string, number> }>();
    for (const sec of CANONICAL_SECTOR_ORDER) {
      map.set(sec, { count: 0, subSectors: new Map() });
    }
    for (const r of activeRows) {
      const sec = r.sector || 'Unclassified';
      const sub = r.sub || 'Unclassified';
      if (!map.has(sec)) {
        map.set(sec, { count: 0, subSectors: new Map() });
      }
      const entry = map.get(sec)!;
      entry.count += 1;
      entry.subSectors.set(sub, (entry.subSectors.get(sub) || 0) + 1);
    }
    return map;
  }, [activeRows]);

  // Sector filtering
  const filteredSectorsList = useMemo(() => {
    const q = sectorSearch.toLowerCase();
    const ordered = [
      ...CANONICAL_SECTOR_ORDER,
      ...Array.from(dynamicSectorsMap.keys()).filter(k => !CANONICAL_SECTOR_ORDER.includes(k)),
    ];
    return ordered.filter(s => {
      const hasCount = (dynamicSectorsMap.get(s)?.count || 0) > 0;
      return (s !== 'Unclassified' || hasCount) && s.toLowerCase().includes(q);
    });
  }, [sectorSearch, dynamicSectorsMap]);

  // Combined Rows after Sector and Numeric Filter Application
  const filteredAndSortedRows = useMemo(() => {
    let result = activeRows;

    // Apply Sector / SubSector filter
    if (selectedSectors.size > 0 || selectedSubSectors.size > 0) {
      result = result.filter(r => {
        if (selectedSubSectors.size > 0 && selectedSubSectors.has(r.sub)) return true;
        if (selectedSectors.size > 0 && selectedSectors.has(r.sector)) return true;
        return false;
      });
    }

    // Apply Numeric Filters (AND combined)
    result = result.filter(r => {
      return filters.every(f => {
        if (f.min === null && f.max === null) return true;
        const val = r.v[f.id];
        if (val === null || val === undefined) return false;
        if (f.min !== null && val < f.min) return false;
        if (f.max !== null && val > f.max) return false;
        return true;
      });
    });

    // Apply Sorting
    return [...result].sort((a, b) => {
      if (sort.id === 'name') {
        return sort.dir * a.name.localeCompare(b.name);
      }
      const valA = a.v[sort.id];
      const valB = b.v[sort.id];
      if (valA === null || valA === undefined) return 1;
      if (valB === null || valB === undefined) return -1;
      return sort.dir * (valA - valB);
    });
  }, [activeRows, selectedSectors, selectedSubSectors, filters, sort]);

  // Metric values helper for range sliders
  const getMetricValues = (metricId: string): number[] => {
    return activeRows
      .map(r => r.v[metricId])
      .filter((x): x is number => x !== null && x !== undefined);
  };

  // Section open/close toggle
  const toggleSection = (id: string) => {
    setOpenSections(prev => {
      const next = new Set(prev);
      if (next.has(id)) next.delete(id);
      else next.add(id);
      return next;
    });
  };

  // Sector selection toggle
  const toggleSector = (sector: string) => {
    setSelectedSectors(prev => {
      const next = new Set(prev);
      if (next.has(sector)) next.delete(sector);
      else next.add(sector);
      return next;
    });
    setIsDirty(true);
  };

  // Sub-sector selection toggle
  const toggleSubSector = (sub: string) => {
    setSelectedSubSectors(prev => {
      const next = new Set(prev);
      if (next.has(sub)) next.delete(sub);
      else next.add(sub);
      return next;
    });
    setIsDirty(true);
  };

  // Filter value change
  const handleFilterChange = (id: string, min: number | null, max: number | null) => {
    setFilters(prev =>
      prev.map(f => (f.id === id ? { ...f, min, max } : f))
    );
    setIsDirty(true);
  };

  // Reset all filters
  const handleResetAll = () => {
    setFilters(prev => prev.map(f => ({ ...f, min: null, max: null })));
    setSelectedSectors(new Set());
    setSelectedSubSectors(new Set());
    setIsDirty(false);
    showToast('Filters reset.');
  };

  // Remove added filter
  const handleRemoveFilter = (id: string) => {
    setFilters(prev => prev.filter(f => f.id !== id));
    setColumns(prev => prev.filter(c => c !== id));
    setIsDirty(true);
  };

  // Add or remove filter from modal
  const handleToggleFilter = (id: string, isChecked: boolean) => {
    if (isChecked) {
      if (!filters.some(f => f.id === id)) {
        setFilters(prev => [...prev, { id, min: null, max: null }]);
      }
      if (!columns.includes(id)) {
        setColumns(prev => [...prev, id]);
      }
      setOpenSections(prev => new Set([...prev, 'f_' + id]));
    } else {
      setFilters(prev => prev.filter(f => f.id !== id));
    }
    setIsDirty(true);
  };

  // Sort click
  const handleHeaderSort = (id: string) => {
    setSort(prev => {
      if (prev.id === id) {
        return { id, dir: prev.dir === 1 ? -1 : 1 };
      }
      return { id, dir: -1 };
    });
  };

  // Excel / CSV File Upload
  const handleFileUpload = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;

    file.arrayBuffer().then(buffer => {
      try {
        const wb = XLSX.read(buffer);
        const firstSheetName = wb.SheetNames[0];
        const rawJson: any[] = XLSX.utils.sheet_to_json(wb.Sheets[firstSheetName], { defval: null });
        if (!rawJson.length) {
          showToast('No rows found in uploaded sheet.');
          return;
        }

        const keys = Object.keys(rawJson[0]);
        const rows: StockRow[] = rawJson.map(o => {
          const row: StockRow = { name: '', sub: '', sector: '', v: {} };
          keys.forEach(k => {
            const cleanKey = k.toLowerCase().trim();
            const val = o[k];
            if (/^(name|company|company_name|stock|symbol)$/i.test(cleanKey)) {
              row.name = String(val ?? '');
            } else if (/^sub_?sector$/i.test(cleanKey)) {
              row.sub = String(val ?? '');
            } else if (/^sector$/i.test(cleanKey)) {
              row.sector = String(val ?? '');
            } else {
              const num = typeof val === 'number' ? val : parseFloat(String(val).replace(/,/g, ''));
              if (!isNaN(num)) {
                const metricId = cleanKey.replace(/[^a-z0-9]+/g, '_');
                row.v[metricId] = num;
              }
            }
          });
          return row;
        });

        const derivedRows = deriveMetrics(rows.map(r => ({
          ...r,
          sub: r.sub || 'Unclassified',
          sector: r.sector || 'Unclassified',
        })));
        const newUniverse: StockUniverse = {
          id: 'custom_' + Date.now(),
          name: file.name,
          type: 'custom',
          rows: derivedRows,
        };

        setUniverses(prev => [...prev, newUniverse]);
        setSelectedUniverseIds(new Set([newUniverse.id]));
        setActiveUniverseTab('custom');
        showToast(`Loaded ${rows.length} stocks from ${file.name}`);
      } catch (err) {
        showToast('Error parsing file.');
      }
    });
    e.target.value = '';
  };

  // Save current screen
  const handleSaveScreen = (name: string, screenNote: string) => {
    const newScreen: SavedScreen = {
      id: 'scr_' + Date.now(),
      name,
      note: screenNote,
      filters: JSON.parse(JSON.stringify(filters)),
      columns: [...columns],
      sort: { ...sort },
      createdAt: new Date().toISOString(),
    };

    const updated = [...savedScreens, newScreen];
    setSavedScreens(updated);
    try {
      localStorage.setItem('screener_saved_screens', JSON.stringify(updated));
    } catch (e) {}
    setIsDirty(false);
    showToast(`Saved "${name}".`);
  };

  // Load screen
  const handleLoadScreen = (screen: SavedScreen) => {
    setFilters(JSON.parse(JSON.stringify(screen.filters)));
    setColumns([...screen.columns]);
    setSort({ ...screen.sort });
    setNote(screen.note || '');
    setIsDirty(false);
    showToast(`Loaded "${screen.name}".`);
  };

  // Delete screen
  const handleDeleteScreen = (id: string) => {
    const updated = savedScreens.filter(s => s.id !== id);
    setSavedScreens(updated);
    try {
      localStorage.setItem('screener_saved_screens', JSON.stringify(updated));
    } catch (e) {}
    showToast('Screen deleted.');
  };

  // Custom filter save
  const handleSaveCustomFilter = (
    name: string,
    formula: string,
    fn: (r: StockRow) => number | null
  ) => {
    const id = 'cf_' + name.toLowerCase().replace(/[^a-z0-9]+/g, '_');
    const newDef: FilterDefinition = {
      id,
      name,
      category: 'Your Filters',
      unit: '',
      in_screenshot: true,
      locked_in_original: false,
      needs_official_source: false,
      availability: 'Computed-from-official',
      formula,
    };

    ALL_FILTERS_MAP.set(id, newDef);
    // Apply custom formula to active rows
    setUniverses(prev =>
      prev.map(u => ({
        ...u,
        rows: u.rows.map(r => {
          const res = fn(r);
          return {
            ...r,
            v: { ...r.v, [id]: res },
          };
        }),
      }))
    );

    // Automatically add as active filter and column
    setFilters(prev => [...prev, { id, min: null, max: null }]);
    if (!columns.includes(id)) {
      setColumns(prev => [...prev, id]);
    }
    setOpenSections(prev => new Set([...prev, 'f_' + id]));
    showToast(`Custom filter "${name}" created.`);
  };

  // Count of active filters
  const activeFiltersCount = filters.filter(f => f.min !== null || f.max !== null).length;

  return (
    <div className="app-container" onClick={() => {
      setIsColumnPickerOpen(false);
      setIsExportMenuOpen(false);
    }}>
      {/* Hidden File Input for Excel Upload */}
      <input
        type="file"
        ref={fileInputRef}
        accept=".xlsx,.xls,.csv"
        style={{ display: 'none' }}
        onChange={handleFileUpload}
      />

      {/* LEFT FILTER PANEL */}
      <div className="left-panel">
        <div className="left-panel-header">
          <span>
            {activeFiltersCount > 0
              ? `${activeFiltersCount} filter${activeFiltersCount > 1 ? 's' : ''} applied`
              : 'No filters applied'}
          </span>
          <button className="btn-outline" onClick={handleResetAll}>
            Reset all
          </button>
        </div>

        <div className="left-panel-body">
          {/* 1. Stock Universe Accordion */}
          <div className="filter-section">
            <div
              className="filter-section-header"
              onClick={() => toggleSection('stock_universe')}
            >
              <span>Stock Universe</span>
              <span>{openSections.has('stock_universe') ? <ChevronUp size={16} /> : <ChevronDown size={16} />}</span>
            </div>

            {openSections.has('stock_universe') && (
              <div className="filter-section-body">
                <div className="universe-tabs">
                  <div style={{ display: 'flex', gap: '12px' }}>
                    <span
                      className={`universe-tab-item ${activeUniverseTab === 'default' ? 'active' : ''}`}
                      onClick={() => setActiveUniverseTab('default')}
                    >
                      Default
                    </span>
                    <span
                      className={`universe-tab-item ${activeUniverseTab === 'custom' ? 'active' : ''}`}
                      onClick={() => setActiveUniverseTab('custom')}
                    >
                      Custom
                    </span>
                  </div>
                  <span
                    className="create-link"
                    onClick={() => setIsExcelUploadOpen(true)}
                  >
                    + Create
                  </span>
                </div>

                {activeUniverseTab === 'default' ? (
                  <div>
                    <div
                      style={{
                        display: 'flex',
                        justifyContent: 'space-between',
                        alignItems: 'center',
                        fontSize: '11px',
                        color: 'var(--text-secondary)',
                        marginBottom: '6px',
                        paddingBottom: '4px',
                        borderBottom: '1px solid var(--border-light)',
                      }}
                      title={
                        isSynced && allListedMeta
                          ? `All NSE + BSE listed: ${allListedMeta.count} securities (As of: ${allListedMeta.as_of || 'n/a'})`
                          : 'Offline sample mode (15 rows)'
                      }
                    >
                      <span>
                        {allListedMeta ? allListedMeta.label : 'All NSE + BSE listed'}
                        {isSynced ? ` (${allListedMeta?.count ?? liveRows.length})` : ''}
                      </span>
                      {selectedIndexSlugs.size > 0 && (
                        <button
                          type="button"
                          className="create-link"
                          style={{ background: 'none', border: 'none', padding: 0, fontSize: '11px' }}
                          onClick={() => {
                            setSelectedIndexSlugs(new Set());
                            setVisibleLimit(20);
                          }}
                        >
                          Show all
                        </button>
                      )}
                    </div>

                    {(showMoreUniverses ? indexUniverses : indexUniverses.slice(0, 5)).map((u) => {
                      const disabled = !isSynced || u.count === 0;
                      const tooltip = isSynced
                        ? `Members: ${u.count} | As of: ${u.as_of || 'n/a'}`
                        : 'Offline sample mode — needs make sync-weekly';
                      return (
                        <label
                          key={u.id}
                          className="universe-checkbox-item"
                          style={{ opacity: disabled ? 0.65 : 1, cursor: disabled ? 'not-allowed' : 'pointer' }}
                          title={tooltip}
                        >
                          <input
                            type="checkbox"
                            disabled={disabled}
                            checked={!disabled && selectedIndexSlugs.has(u.slug)}
                            onChange={() => toggleIndexSelection(u.slug)}
                          />
                          <span style={{ flex: 1 }}>
                            {u.label}
                            {isSynced && u.count > 0 ? ` (${u.count})` : ''}
                          </span>
                          {(!isSynced || u.count === 0) && (
                            <span
                              style={{
                                fontSize: '10px',
                                color: 'var(--text-muted)',
                                background: 'var(--tag-bg)',
                                padding: '1px 5px',
                                borderRadius: '3px',
                              }}
                            >
                              needs sync
                            </span>
                          )}
                        </label>
                      );
                    })}

                    {indexUniverses.length > 5 && (
                      <span
                        className="show-more-link"
                        onClick={() => setShowMoreUniverses(!showMoreUniverses)}
                      >
                        {showMoreUniverses ? 'Show Less' : `Show ${indexUniverses.length - 5} More`}
                      </span>
                    )}
                  </div>
                ) : (
                  <div>
                    {universes.filter(u => u.type === 'custom').length === 0 ? (
                      <div style={{ fontSize: '12px', color: 'var(--text-muted)', padding: '6px 0' }}>
                        No custom universes uploaded yet. Click "+ Create" above.
                      </div>
                    ) : (
                      universes
                        .filter(u => u.type === 'custom')
                        .map((u) => (
                          <div
                            key={u.id}
                            style={{
                              display: 'flex',
                              alignItems: 'center',
                              justifyContent: 'space-between',
                              padding: '3px 0',
                            }}
                          >
                            <label className="universe-checkbox-item" style={{ flex: 1, marginBottom: 0 }}>
                              <input
                                type="checkbox"
                                checked={selectedUniverseIds.has(u.id)}
                                onChange={() => toggleUniverseSelection(u.id)}
                              />
                              <span title={u.name} style={{ overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap', maxWidth: '160px' }}>
                                {u.name}
                              </span>
                            </label>
                            <div style={{ display: 'flex', gap: '6px', alignItems: 'center' }}>
                              <span style={{ fontSize: '11px', color: 'var(--text-muted)' }}>({u.rows.length})</span>
                              <button
                                type="button"
                                style={{ background: 'none', border: 'none', cursor: 'pointer', color: 'var(--text-muted)', padding: '2px' }}
                                title="Rename universe"
                                onClick={() => handleRenameUniverse(u.id, u.name)}
                              >
                                <Pencil size={12} />
                              </button>
                              <button
                                type="button"
                                style={{ background: 'none', border: 'none', cursor: 'pointer', color: 'var(--text-muted)', padding: '2px' }}
                                title="Delete universe"
                                onClick={() => handleDeleteUniverse(u.id)}
                              >
                                <Trash2 size={12} />
                              </button>
                            </div>
                          </div>
                        ))
                    )}
                  </div>
                )}
              </div>
            )}
          </div>

          {/* 2. Sector Accordion */}
          <div className="filter-section">
            <div
              className="filter-section-header"
              onClick={() => toggleSection('sector')}
            >
              <span>Sector</span>
              <span>{openSections.has('sector') ? <ChevronUp size={16} /> : <ChevronDown size={16} />}</span>
            </div>

            {openSections.has('sector') && (
              <div className="filter-section-body">
                <div className="sector-search-box">
                  <Search size={14} className="sector-search-icon" />
                  <input
                    type="text"
                    placeholder="Search by sector name"
                    value={sectorSearch}
                    onChange={e => setSectorSearch(e.target.value)}
                  />
                </div>

                <div style={{ maxHeight: '280px', overflowY: 'auto' }}>
                  {filteredSectorsList.map(secName => {
                    const secData = dynamicSectorsMap.get(secName);
                    const isSecChecked = selectedSectors.has(secName);
                    const isSecExpanded = expandedSectors.has(secName);
                    const subEntries = secData ? Array.from(secData.subSectors.entries()).sort((a, b) => b[1] - a[1]) : [];

                    return (
                      <div key={secName}>
                        <div className="sector-row">
                          <label className="sector-row-left">
                            <input
                              type="checkbox"
                              checked={isSecChecked}
                              onChange={() => toggleSector(secName)}
                            />
                            <span>
                              {secName} ({secData?.count ?? 0})
                            </span>
                          </label>
                          {subEntries.length > 0 && (
                            <span
                              className="sector-expand-chevron"
                              onClick={() => {
                                setExpandedSectors(prev => {
                                  const next = new Set(prev);
                                  if (next.has(secName)) next.delete(secName);
                                  else next.add(secName);
                                  return next;
                                });
                              }}
                            >
                              {isSecExpanded ? <ChevronUp size={14} /> : <ChevronDown size={14} />}
                            </span>
                          )}
                        </div>

                        {/* Sub-Sectors Expansion */}
                        {isSecExpanded && subEntries.length > 0 && (
                          <div className="subsector-list">
                            {subEntries.map(([subName, subCount]) => (
                              <label key={subName} className="universe-checkbox-item">
                                <input
                                  type="checkbox"
                                  checked={selectedSubSectors.has(subName)}
                                  onChange={() => toggleSubSector(subName)}
                                />
                                <span style={{ fontSize: '12px' }}>
                                  {subName} ({subCount})
                                </span>
                              </label>
                            ))}
                          </div>
                        )}
                      </div>
                    );
                  })}
                </div>
              </div>
            )}
          </div>

          {/* 3. Numeric Filter Widgets */}
          {filters.map(fState => {
            const filterDef = ALL_FILTERS_MAP.get(fState.id) || {
              id: fState.id,
              name: fState.id,
              category: 'Custom',
              unit: '',
              in_screenshot: true,
              locked_in_original: false,
              needs_official_source: true,
              availability: 'Computed-from-official',
            };
            const secKey = 'f_' + fState.id;
            const isOpen = openSections.has(secKey);
            const vals = getMetricValues(fState.id);
            const isRemovable = !DEFAULT_FILTER_IDS.includes(fState.id);

            return (
              <NumericFilterWidget
                key={fState.id}
                filter={filterDef}
                isOpen={isOpen}
                onToggleOpen={() => toggleSection(secKey)}
                currentMin={fState.min}
                currentMax={fState.max}
                values={vals}
                onFilterChange={(min, max) => handleFilterChange(fState.id, min, max)}
                onRemove={() => handleRemoveFilter(fState.id)}
                isRemovable={isRemovable}
              />
            );
          })}
        </div>

        {/* Pinned Bottom Add Filter Button */}
        <div className="left-panel-footer">
          <button
            className="btn-add-filter"
            onClick={() => setIsAddFilterModalOpen(true)}
          >
            + Add Filter
          </button>
        </div>
      </div>

      {/* RIGHT RESULTS PANE */}
      <div className="right-pane">
        {/* Top Header */}
        <div className="screener-top-header">
          <div className="screener-title-area">
            <h1 className="screener-title">Stock Screener</h1>
            <input
              type="text"
              className="screener-note-input"
              placeholder="Add a note to remember why you created this - e.g., “Large-cap, low PE”, “Auto sector picks” or “Tracking renewable energy”."
              value={note}
              onChange={e => {
                setNote(e.target.value);
                setIsDirty(true);
              }}
            />
          </div>

          <div className="screener-header-actions">
            <button
              className="btn-outline"
              title="Toggle Theme"
              onClick={toggleTheme}
            >
              {theme === 'light' ? <Moon size={15} /> : <Sun size={15} />}
            </button>
            <button
              className="btn-outline"
              title="Edit Note"
              onClick={() => document.querySelector<HTMLInputElement>('.screener-note-input')?.focus()}
            >
              <Pencil size={15} />
            </button>
            <button
              className="btn-outline"
              title="Saved Screens & Share"
              onClick={() => setIsSavedScreensModalOpen(true)}
            >
              <Share2 size={15} />
            </button>
            <button
              className="btn-primary"
              disabled={!isDirty && savedScreens.length > 0}
              onClick={() => setIsSavedScreensModalOpen(true)}
            >
              Save
            </button>
          </div>
        </div>

        {/* Sub Bar */}
        <div className="screener-sub-bar">
          <span className="results-count-text">
            Showing <b>{filteredAndSortedRows.length === 0 ? 0 : 1} - {Math.min(visibleLimit, filteredAndSortedRows.length)}</b> of <b>{filteredAndSortedRows.length}</b> results
          </span>

          <div className="sub-bar-right">
            <div
              className="update-time-info"
              title={isSynced && liveSyncSourceLabel ? liveSyncSourceLabel : 'Offline sample mode: 15 fixture rows until sync'}
            >
              <Clock size={13} />
              <span>{isSynced ? (liveSyncSourceLabel || 'Official DuckDB synced') : 'Offline sample mode'}</span>
            </div>

            <div style={{ position: 'relative' }}>
              <button
                className="btn-outline btn-export"
                onClick={e => {
                  e.stopPropagation();
                  setIsExportMenuOpen(!isExportMenuOpen);
                }}
              >
                Export
              </button>

              <ExportMenu
                isOpen={isExportMenuOpen}
                onClose={() => setIsExportMenuOpen(false)}
                onExportCsv={() => exportTableData(filteredAndSortedRows, columns, ALL_FILTERS_MAP, 'csv')}
                onExportXlsx={() => exportTableData(filteredAndSortedRows, columns, ALL_FILTERS_MAP, 'xlsx')}
                onCopyCsv={() => {
                  const headers = ['Name', 'Sub-Sector', ...columns.map(c => ALL_FILTERS_MAP.get(c)?.name || c)];
                  const rows = filteredAndSortedRows.map(r => [
                    r.name,
                    r.sub,
                    ...columns.map(c => r.v[c] ?? ''),
                  ]);
                  const csv = [headers, ...rows].map(a => a.map(x => `"${String(x).replace(/"/g, '""')}"`).join(',')).join('\n');
                  navigator.clipboard.writeText(csv);
                  showToast('Copied CSV to clipboard!');
                }}
              />
            </div>

            <span className="blue-dot-indicator" title="Live status indicator" />
          </div>
        </div>

        {/* Offline Sample Banner when DuckDB is not synced */}
        {!isSynced && (
          <div
            data-testid="sample-mode-banner"
            style={{
              padding: '7px 20px',
              fontSize: '12px',
              background: '#fffbeb',
              borderBottom: '1px solid #fde68a',
              color: '#92400e',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'space-between',
            }}
          >
            <span>
              Offline sample mode: {INITIAL_SEED_ROWS.length} sample rows. Run{' '}
              <code style={{ background: 'rgba(146, 64, 14, 0.1)', padding: '1px 4px', borderRadius: '3px' }}>make sync-weekly</code>{' '}
              and{' '}
              <code style={{ background: 'rgba(146, 64, 14, 0.1)', padding: '1px 4px', borderRadius: '3px' }}>make sync-daily</code>, then reload.
            </span>
          </div>
        )}

        {/* Toast notification banner */}
        {toastMessage && (
          <div
            style={{
              padding: '6px 20px',
              fontSize: '12px',
              background: 'var(--panel-secondary)',
              borderBottom: '1px solid var(--border)',
              color: 'var(--text-secondary)',
            }}
          >
            {toastMessage}
          </div>
        )}

        {/* Table Area (Infinite scroll pagination with page size 20) */}
        <div
          className="table-wrapper"
          onScroll={(e) => {
            const el = e.currentTarget;
            if (el.scrollTop + el.clientHeight >= el.scrollHeight - 40 && visibleLimit < filteredAndSortedRows.length) {
              setVisibleLimit((prev) => Math.min(filteredAndSortedRows.length, prev + 20));
            }
          }}
        >
          <table className="screener-table">
            <thead>
              <tr>
                <th
                  className="col-picker"
                  title="Configure columns"
                  onClick={e => {
                    e.stopPropagation();
                    setIsColumnPickerOpen(!isColumnPickerOpen);
                  }}
                  style={{ fontSize: '15px' }}
                >
                  ⊕
                </th>
                <th className="col-name" onClick={() => handleHeaderSort('name')}>
                  Name {sort.id === 'name' && (sort.dir === 1 ? '↑' : '↓')}
                </th>
                <th className="col-subsector">Sub-Sector</th>

                {columns.map(colId => {
                  const fDef = ALL_FILTERS_MAP.get(colId);
                  const isSorted = sort.id === colId;
                  const label = fDef ? fDef.name : colId;

                  return (
                    <th key={colId} onClick={() => handleHeaderSort(colId)}>
                      {isSorted && (sort.dir === -1 ? '↓ ' : '↑ ')}
                      {label}
                    </th>
                  );
                })}
              </tr>
            </thead>
            <tbody>
              {filteredAndSortedRows.length === 0 ? (
                <tr>
                  <td
                    colSpan={columns.length + 3}
                    style={{ textAlign: 'center', padding: '40px', color: 'var(--text-muted)' }}
                  >
                    No stocks match the selected filters.
                  </td>
                </tr>
              ) : (
                filteredAndSortedRows.slice(0, visibleLimit).map((stock, idx) => (
                  <tr key={stock.name} onClick={() => setSelectedStock(stock)}>
                    <td className="col-index">{idx + 1}.</td>
                    <td className="col-name">{stock.name}</td>
                    <td className="col-subsector">{stock.sub}</td>

                    {columns.map(colId => {
                      const val = stock.v[colId];
                      const fDef = ALL_FILTERS_MAP.get(colId);
                      const prov = stock._provenance || {};
                      const isBankOrInsurer = /bank|insur/i.test(`${stock.sector} ${stock.sub}`);
                      const isSectorNa = (val === null || val === undefined) && isBankOrInsurer && BANK_INSURER_INAPPLICABLE_IDS.has(colId);
                      const cellTooltip = val === null || val === undefined
                        ? (
                          isSectorNa
                            ? `${fDef?.name || colId}: n/a for this sector`
                            : (isSynced && fDef?.feeds === 'history' && (prov.px_days ?? 0) > 0
                              ? `${fDef.name}: null — insufficient history (${prov.px_days} trading days stored)`
                              : `${fDef?.name || colId}: ${formatMissingFeedReason(fDef?.feeds)}`)
                        )
                        : colId === 'market_cap'
                          ? `Market Cap: ${formatIndianNumber(val)} Rs Cr | Shares: ${prov.shares_source || 'official'} (${prov.shares_as_of || 'n/a'}) | Price: ${prov.price_source || 'NSE'} (${prov.price_as_of || 'n/a'})`
                          : `${fDef?.name || colId}: ${formatIndianNumber(val)} | Source: ${prov.price_source || fDef?.feeds || 'official'} | As of: ${prov.price_as_of || 'fixture'}`;
                      return (
                        <td key={colId} title={cellTooltip}>
                          {isSectorNa ? 'n/a (sector)' : formatIndianNumber(val)}
                        </td>
                      );
                    })}
                  </tr>
                ))
              )}
            </tbody>
          </table>

          {/* Column Picker Popup */}
          <ColumnPicker
            isOpen={isColumnPickerOpen}
            onClose={() => setIsColumnPickerOpen(false)}
            availableFilters={ALL_FILTERS_LIST}
            loadedFilterIds={loadedFilterIds}
            activeColumns={columns}
            onToggleColumn={(id, checked) => {
              if (checked) {
                if (!columns.includes(id)) setColumns(prev => [...prev, id]);
              } else {
                setColumns(prev => prev.filter(c => c !== id));
              }
              setIsDirty(true);
            }}
          />
        </div>

        {/* Stock Detail Drawer Shell */}
        <StockDetailDrawer
          stock={selectedStock}
          onClose={() => setSelectedStock(null)}
          filterMap={ALL_FILTERS_MAP}
        />
      </div>

      {/* Add Filters Modal */}
      <AddFiltersModal
        isOpen={isAddFilterModalOpen}
        onClose={() => setIsAddFilterModalOpen(false)}
        initialCategory={modalCategory}
        allFilters={ALL_FILTERS_LIST}
        activeFilterIds={filters.map(f => f.id)}
        loadedFilterIds={loadedFilterIds}
        filterCoverage={filterCoverage}
        onToggleFilter={handleToggleFilter}
        onOpenCustomFilterBuilder={() => {
          setIsAddFilterModalOpen(false);
          setIsCustomFilterModalOpen(true);
        }}
        onOpenGlossary={cat => {
          setGlossaryCategory(cat);
          setIsGlossaryModalOpen(true);
        }}
      />

      {/* In-App Glossary Modal */}
      <GlossaryModal
        isOpen={isGlossaryModalOpen}
        onClose={() => setIsGlossaryModalOpen(false)}
        category={glossaryCategory}
        filters={ALL_FILTERS_LIST}
      />

      {/* Custom Filter Builder Modal */}
      <CustomFilterModal
        isOpen={isCustomFilterModalOpen}
        onClose={() => setIsCustomFilterModalOpen(false)}
        filterMap={ALL_FILTERS_MAP}
        sampleRows={activeRows}
        onSaveFilter={handleSaveCustomFilter}
      />

      {/* Saved Screens Modal */}
      <SavedScreensModal
        isOpen={isSavedScreensModalOpen}
        onClose={() => setIsSavedScreensModalOpen(false)}
        savedScreens={savedScreens}
        currentNote={note}
        currentFilters={filters}
        currentColumns={columns}
        currentSort={sort}
        onLoadScreen={handleLoadScreen}
        onSaveCurrentScreen={handleSaveScreen}
        onDeleteScreen={handleDeleteScreen}
      />

      {/* Excel Universe Upload Modal */}
      <ExcelUploadModal
        isOpen={isExcelUploadOpen}
        onClose={() => setIsExcelUploadOpen(false)}
        onProceedToMatch={handleProceedToMatch}
      />

      {/* Security Master Match Report Modal */}
      <MatchReportModal
        isOpen={isMatchReportOpen}
        report={matchReportData}
        defaultUniverseName={uploadedFilename}
        onClose={() => setIsMatchReportOpen(false)}
        onSaveUniverse={handleSaveCustomUniverse}
      />
    </div>
  );
};

export default App;
