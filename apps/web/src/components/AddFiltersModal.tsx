import React, { useState } from 'react';
import { FilterDefinition } from '../types';
import { Search, ChevronRight, Lock, BookOpen } from 'lucide-react';

export interface FilterCoverageStats {
  nonNull: number;
  total: number;
  pct: number;
}

export function formatMissingFeedReason(feeds?: string): string {
  switch (feeds) {
    case 'daily':
      return 'needs make sync-daily';
    case 'weekly':
      return 'needs make sync-weekly';
    case 'shp':
      return 'needs make sync-shp';
    case 'history':
      return 'needs make backfill';
    case 'xbrl':
      return 'needs make sync-quarterly';
    case 'fno':
      return 'needs F&O bhavcopy';
    case 'deals':
      return 'needs make sync-deals';
    case 'amfi':
      return 'needs AMFI TER / NAV';
    case 'manual':
      return 'needs data/inbox/fbil_mibor.json';
    case 'inbox':
      return 'needs data/inbox/ drop';
    case 'unavailable':
      return 'Not available from official sources';
    default:
      return 'needs sync';
  }
}

interface AddFiltersModalProps {
  isOpen: boolean;
  onClose: () => void;
  allFilters: FilterDefinition[];
  activeFilterIds: string[];
  loadedFilterIds: Set<string>;
  filterCoverage?: Map<string, FilterCoverageStats>;
  onToggleFilter: (id: string, isChecked: boolean) => void;
  onOpenCustomFilterBuilder: () => void;
  onOpenGlossary: (category: string) => void;
  initialCategory?: string;
}

export const CATEGORIES_ORDER = [
  'Profitability',
  'Growth',
  'Valuation',
  'Ownership',
  'Futures & Options',
  'Price and Volume',
  'Financial Ratios',
  'Special',
  'Analyst Ratings',
  'Technical Indicators',
  'Balance Sheet & Cash Flow',
  'ETFs',
  'Income Statement',
  'Your Filters',
];

export const AddFiltersModal: React.FC<AddFiltersModalProps> = ({
  isOpen,
  onClose,
  allFilters,
  activeFilterIds,
  loadedFilterIds,
  filterCoverage,
  onToggleFilter,
  onOpenCustomFilterBuilder,
  onOpenGlossary,
  initialCategory,
}) => {
  const [selectedCategory, setSelectedCategory] = useState<string>(initialCategory || 'Profitability');
  const [searchQuery, setSearchQuery] = useState<string>('');

  React.useEffect(() => {
    if (initialCategory) {
      setSelectedCategory(initialCategory);
    }
  }, [initialCategory]);

  if (!isOpen) return null;

  // Filter items based on search or category
  const filteredItems = searchQuery
    ? allFilters.filter(f =>
        f.name.toLowerCase().includes(searchQuery.toLowerCase())
      )
    : allFilters.filter(f => f.category === selectedCategory);

  const isYourFilters = !searchQuery && selectedCategory === 'Your Filters';

  return (
    <div className="modal-overlay">
      <div className="modal-header">
        <div className="modal-title-area">
          <b>Add Filters</b>
          <div className="modal-subtitle">Pick from over 200 filters</div>
        </div>
        <div className="modal-header-right">
          <button className="btn-outline" onClick={onOpenCustomFilterBuilder}>
            Custom
          </button>
          <div style={{ position: 'relative' }}>
            <input
              type="text"
              placeholder="Search for Filters"
              value={searchQuery}
              onChange={e => setSearchQuery(e.target.value)}
              style={{ width: '160px', paddingRight: '26px' }}
            />
            <Search
              size={14}
              style={{
                position: 'absolute',
                right: 8,
                top: '50%',
                transform: 'translateY(-50%)',
                color: 'var(--text-muted)',
                pointerEvents: 'none',
              }}
            />
          </div>
        </div>
      </div>

      <div className="modal-body">
        {/* Category Rail */}
        <div className="modal-rail">
          {CATEGORIES_ORDER.map(cat => {
            const isActive = !searchQuery && selectedCategory === cat;
            return (
              <div
                key={cat}
                className={`modal-rail-item ${isActive ? 'active' : ''}`}
                onClick={() => {
                  setSelectedCategory(cat);
                  setSearchQuery('');
                }}
              >
                <span>{cat === 'Special' ? 'Quant Special' : cat}</span>
                {isActive && <ChevronRight size={14} />}
              </div>
            );
          })}
        </div>

        {/* Content Area */}
        <div className="modal-content-area">
          {isYourFilters ? (
            /* Screenshot 21 - Your Filters Onboarding View */
            <div className="your-filters-card">
              <div className="your-filters-text">
                Create your custom filter by using existing filters and operators like + , - , * and /
              </div>
              <button
                className="btn-outline"
                style={{ padding: '8px 16px', fontWeight: 600 }}
                onClick={onOpenCustomFilterBuilder}
              >
                Create Custom Filter
              </button>
            </div>
          ) : (
            <div>
              {filteredItems.length === 0 ? (
                <div style={{ padding: '20px', color: 'var(--text-muted)', textAlign: 'center' }}>
                  No filters found
                </div>
              ) : (
                filteredItems.map(filter => {
                  const isChecked = activeFilterIds.includes(filter.id);
                  const cov = filterCoverage?.get(filter.id);
                  const nonNull = cov ? cov.nonNull : loadedFilterIds.has(filter.id) ? 1 : 0;
                  const hasData = nonNull > 0;
                  const isUnavailable = filter.availability === 'Unavailable' || filter.feeds === 'unavailable';
                  const isApprox = filter.availability === 'Approximate';
                  const tooltip = cov && cov.nonNull > 0
                    ? `Coverage: ${cov.pct.toFixed(1)}% (${cov.nonNull}/${cov.total}) — ${filter.formula || filter.name}`
                    : (filter.formula || filter.name);
                  const missingText = formatMissingFeedReason(filter.feeds);

                  return (
                    <label key={filter.id} className="modal-filter-item">
                      <input
                        type="checkbox"
                        checked={isChecked}
                        onChange={e => onToggleFilter(filter.id, e.target.checked)}
                      />
                      <span style={{ flex: 1 }} title={tooltip}>{filter.name}</span>
                      {isApprox && (
                        <span
                          style={{
                            fontSize: '10px',
                            color: '#b45309',
                            background: 'rgba(245, 158, 11, 0.14)',
                            padding: '2px 6px',
                            borderRadius: '3px',
                            fontWeight: 500,
                          }}
                        >
                          Approximate - computed locally
                        </span>
                      )}
                      {isUnavailable ? (
                        <span
                          style={{
                            fontSize: '10px',
                            color: '#6b7280',
                            background: 'var(--tag-bg)',
                            padding: '2px 6px',
                            borderRadius: '3px',
                          }}
                        >
                          Not available from official sources
                        </span>
                      ) : !hasData ? (
                        <span
                          style={{
                            fontSize: '10px',
                            color: 'var(--text-muted)',
                            background: 'var(--tag-bg)',
                            padding: '2px 6px',
                            borderRadius: '3px',
                          }}
                        >
                          {missingText}
                        </span>
                      ) : null}
                    </label>
                  );
                })
              )}
            </div>
          )}
        </div>
      </div>

      <div className="modal-footer">
        <div
          className="modal-footer-link"
          onClick={() => {
            if (isYourFilters) {
              onOpenCustomFilterBuilder();
            } else {
              onOpenGlossary(selectedCategory);
            }
          }}
        >
          <BookOpen size={15} color="var(--link-teal)" />
          <span>
            {isYourFilters
              ? 'See how to create Your Filters'
              : `Learn more about ${selectedCategory === 'Special' ? 'Quant Special' : selectedCategory}`}
          </span>
        </div>
        <button className="btn-primary" onClick={onClose}>
          Done
        </button>
      </div>
    </div>
  );
};
