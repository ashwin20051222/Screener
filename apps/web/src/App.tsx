import React, { useState, useMemo, useEffect, useRef } from 'react';
import filtersData from './data/filters.json';
import {
  FilterDefinition,
  FilterState,
  StockRow,
  StockUniverse,
  SavedScreen,
} from './types';
import {
  INITIAL_SEED_ROWS,
  SECTORS_CONFIG,
  deriveMetrics,
} from './data/seed';
import { NumericFilterWidget } from './components/NumericFilterWidget';
import { AddFiltersModal } from './components/AddFiltersModal';
import { GlossaryModal } from './components/GlossaryModal';
import { CustomFilterModal } from './components/CustomFilterModal';
import { StockDetailDrawer } from './components/StockDetailDrawer';
import { SavedScreensModal } from './components/SavedScreensModal';
import { ColumnPicker } from './components/ColumnPicker';
import { ExportMenu } from './components/ExportMenu';
import { exportTableData } from './utils/export';
import { formatIndianNumber } from './utils/formatters';
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
} from 'lucide-react';
import * as XLSX from 'xlsx';

// Load filter definitions
const ALL_FILTERS_MAP = new Map<string, FilterDefinition>(
  Object.entries(filtersData.filters).map(([k, v]) => [k, v as FilterDefinition])
);
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

export const App: React.FC = () => {
  // Theme state
  const [theme, setTheme] = useState<'light' | 'dark'>('light');

  // Stock Universes
  const [universes, setUniverses] = useState<StockUniverse[]>([
    {
      id: 'default_seed',
      name: 'Sample: 15 rows from your screenshots',
      type: 'default',
      rows: INITIAL_SEED_ROWS,
      totalMarketCount: 5996,
    },
  ]);
  const [activeUniverseTab, setActiveUniverseTab] = useState<'default' | 'custom'>('default');
  const [selectedUniverseIndex, setSelectedUniverseIndex] = useState<number | null>(null);
  const activeUniverse = (selectedUniverseIndex !== null ? universes[selectedUniverseIndex] : universes[0]) || universes[0];
  const activeRows = activeUniverse.rows;
  const [showMoreUniverses, setShowMoreUniverses] = useState(false);

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

  // Note & Saved Screens
  const [note, setNote] = useState('');
  const [savedScreens, setSavedScreens] = useState<SavedScreen[]>([]);
  const [isDirty, setIsDirty] = useState(false);
  const [selectedStock, setSelectedStock] = useState<StockRow | null>(null);

  // Synchronous initialization from URL params for Visual QA
  const getInitialParam = (k: string) => {
    try {
      return new URLSearchParams(window.location.search).get(k);
    } catch {
      return null;
    }
  };

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


  // Set of loaded metric IDs
  const loadedFilterIds = useMemo(() => {
    const ids = new Set<string>();
    activeRows.forEach(r => {
      Object.keys(r.v).forEach(k => {
        if (r.v[k] !== null && r.v[k] !== undefined) ids.add(k);
      });
    });
    return ids;
  }, [activeRows]);

  // Sector filtering
  const filteredSectorsList = useMemo(() => {
    const q = sectorSearch.toLowerCase();
    return Object.keys(SECTORS_CONFIG).filter(s => s.toLowerCase().includes(q));
  }, [sectorSearch]);

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

        const derivedRows = deriveMetrics(rows);
        const newUniverse: StockUniverse = {
          id: 'custom_' + Date.now(),
          name: file.name,
          type: 'custom',
          rows: derivedRows,
          totalMarketCount: rows.length,
        };

        setUniverses(prev => [...prev, newUniverse]);
        setSelectedUniverseIndex(universes.length);
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
                    onClick={() => fileInputRef.current?.click()}
                  >
                    + Create
                  </span>
                </div>

                {activeUniverseTab === 'default' ? (
                  <div>
                    <label className="universe-checkbox-item">
                      <input
                        type="checkbox"
                        checked={selectedUniverseIndex === 0}
                        onChange={() => setSelectedUniverseIndex(selectedUniverseIndex === 0 ? null : 0)}
                      />
                      <span>Nifty Smallcap 100</span>
                    </label>
                    <label className="universe-checkbox-item">
                      <input type="checkbox" />
                      <span>Nifty 500</span>
                    </label>
                    <label className="universe-checkbox-item">
                      <input type="checkbox" />
                      <span>Nifty Midcap 100</span>
                    </label>

                    {showMoreUniverses && (
                      <>
                        <label className="universe-checkbox-item">
                          <input type="checkbox" />
                          <span>Nifty 50</span>
                        </label>
                        <label className="universe-checkbox-item">
                          <input type="checkbox" />
                          <span>Nifty 100</span>
                        </label>
                      </>
                    )}

                    <span
                      className="show-more-link"
                      onClick={() => setShowMoreUniverses(!showMoreUniverses)}
                    >
                      {showMoreUniverses ? 'Show Less' : 'Show 2 More'}
                    </span>
                  </div>
                ) : (
                  <div>
                    {universes.filter(u => u.type === 'custom').length === 0 ? (
                      <div style={{ fontSize: '12px', color: 'var(--text-muted)', padding: '6px 0' }}>
                        No custom universes uploaded yet. Click "+ Create" above.
                      </div>
                    ) : (
                      universes.map((u, i) =>
                        u.type === 'custom' ? (
                          <label key={u.id} className="universe-checkbox-item">
                            <input
                              type="checkbox"
                              checked={selectedUniverseIndex === i}
                              onChange={() => setSelectedUniverseIndex(i)}
                            />
                            <span>{u.name}</span>
                          </label>
                        ) : null
                      )
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
                    const secData = SECTORS_CONFIG[secName];
                    const isSecChecked = selectedSectors.has(secName);
                    const isSecExpanded = expandedSectors.has(secName);

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
                        </div>

                        {/* Sub-Sectors Expansion */}
                        {isSecExpanded && secData?.subSectors && (
                          <div className="subsector-list">
                            {Object.entries(secData.subSectors).map(([subName, subCount]) => (
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
            Showing <b>1 - {filteredAndSortedRows.length}</b> of <b>{activeUniverse.totalMarketCount ?? 5996}</b> results
          </span>

          <div className="sub-bar-right">
            <div className="update-time-info">
              <Clock size={13} />
              <span>last updated at 6:30 AM IST</span>
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

        {/* Table Area */}
        <div className="table-wrapper">
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
                filteredAndSortedRows.map((stock, idx) => (
                  <tr key={stock.name} onClick={() => setSelectedStock(stock)}>
                    <td className="col-index">{idx + 1}.</td>
                    <td className="col-name">{stock.name}</td>
                    <td className="col-subsector">{stock.sub}</td>

                    {columns.map(colId => {
                      const val = stock.v[colId];
                      return (
                        <td key={colId}>
                          {formatIndianNumber(val)}
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
    </div>
  );
};

export default App;
