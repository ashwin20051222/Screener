import React, { useState } from 'react';
import { FilterDefinition } from '../types';
import { Search, ChevronRight, Lock, BookOpen } from 'lucide-react';

interface AddFiltersModalProps {
  isOpen: boolean;
  onClose: () => void;
  allFilters: FilterDefinition[];
  activeFilterIds: string[];
  loadedFilterIds: Set<string>;
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
                <span>{cat === 'Special' ? 'Tickertape Special' : cat}</span>
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
                  const hasData = loadedFilterIds.has(filter.id);

                  return (
                    <label key={filter.id} className="modal-filter-item">
                      {filter.locked_in_original ? (
                        <span title="Locked in original (unlocked in this replica)">
                          <input
                            type="checkbox"
                            checked={isChecked}
                            onChange={e => onToggleFilter(filter.id, e.target.checked)}
                          />
                        </span>
                      ) : (
                        <input
                          type="checkbox"
                          checked={isChecked}
                          onChange={e => onToggleFilter(filter.id, e.target.checked)}
                        />
                      )}
                      <span style={{ flex: 1 }}>{filter.name}</span>
                      {filter.locked_in_original && (
                        <span title="Premium in original" style={{ display: 'inline-flex', alignItems: 'center' }}>
                          <Lock size={12} className="modal-filter-lock" />
                        </span>
                      )}
                      {!hasData && (
                        <span
                          style={{
                            fontSize: '11px',
                            color: 'var(--text-muted)',
                            background: 'var(--tag-bg)',
                            padding: '2px 6px',
                            borderRadius: '3px',
                          }}
                        >
                          no data
                        </span>
                      )}
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
              : `Learn more about ${selectedCategory === 'Special' ? 'Tickertape Special' : selectedCategory}`}
          </span>
        </div>
        <button className="btn-primary" onClick={onClose}>
          Done
        </button>
      </div>
    </div>
  );
};
