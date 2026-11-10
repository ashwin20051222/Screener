import React, { useState } from 'react';
import { DataEnsureJob, FilterBackendStatus, FilterDefinition } from '../types';
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
  backendCoverage?: Record<string, FilterBackendStatus>;
  activeJobs?: Record<string, DataEnsureJob>;
  checkingFilters?: Set<string>;
  onToggleFilter: (id: string, isChecked: boolean) => void;
  onRetryFilter?: (id: string) => void;
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
  backendCoverage,
  activeJobs,
  checkingFilters,
  onToggleFilter,
  onRetryFilter,
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
                  const bCov = backendCoverage?.[filter.id];
                  const isChecking = Boolean(checkingFilters?.has(filter.id));
                  const matchingJob = Object.values(activeJobs || {}).find(
                    j => (j.filter_ids.includes(filter.id) || (filter.sync_job && j.sync_job === filter.sync_job))
                      && (j.status === 'queued' || j.status === 'running' || j.status === 'blocked')
                  ) || bCov?.active_job || undefined;

                  const nonNull = cov ? cov.nonNull : (bCov ? bCov.populated_count : (loadedFilterIds.has(filter.id) ? 1 : 0));
                  const eligTotal = bCov ? bCov.eligible_count : (cov?.total || 0);
                  const hasData = nonNull > 0;
                  const isUnavailable = filter.availability === 'Unavailable' || filter.feeds === 'unavailable';
                  const isApprox = filter.availability === 'Approximate';
                  const statusKind = isChecking
                    ? 'checking'
                    : (matchingJob?.status === 'queued' || matchingJob?.status === 'running')
                      ? matchingJob.status
                      : (matchingJob?.status === 'blocked')
                        ? 'blocked'
                        : (bCov?.status || (isUnavailable ? 'unavailable' : (hasData ? 'available' : 'awaiting_sync')));

                  const tooltip = [
                    filter.name,
                    bCov?.status_reason || (cov && cov.nonNull > 0 ? `Coverage: ${cov.pct.toFixed(1)}% (${cov.nonNull}/${cov.total})` : null),
                    filter.primary_source ? `Source: ${filter.primary_source}` : null,
                    filter.refresh_cadence ? `Cadence: ${filter.refresh_cadence}` : null,
                    filter.formula ? `Formula: ${filter.formula}` : null,
                  ].filter(Boolean).join(' · ');

                  let pillText: string | null = null;
                  let pillBg = 'var(--tag-bg)';
                  let pillColor = 'var(--text-muted)';
                  let showRetry = false;

                  if (statusKind === 'checking') {
                    pillText = 'Checking data…';
                    pillBg = 'rgba(20, 184, 166, 0.14)';
                    pillColor = 'var(--link-teal)';
                  } else if (statusKind === 'queued' || statusKind === 'running') {
                    const prog = matchingJob && matchingJob.total > 1
                      ? ` ${matchingJob.processed}/${matchingJob.total}`
                      : '';
                    pillText = `Syncing${prog}…`;
                    pillBg = 'rgba(14, 165, 233, 0.14)';
                    pillColor = '#0284c7';
                  } else if (statusKind === 'blocked') {
                    pillText = 'Rate-limited (403/429)';
                    pillBg = 'rgba(239, 68, 68, 0.12)';
                    pillColor = '#dc2626';
                    showRetry = true;
                  } else if (statusKind === 'unavailable') {
                    pillText = 'Not available from official sources';
                    pillColor = '#6b7280';
                  } else if (statusKind === 'not_applicable') {
                    pillText = 'Not applicable in universe';
                    pillColor = '#64748b';
                  } else if (statusKind === 'manual_required') {
                    pillText = 'Manual source required';
                    pillBg = 'rgba(245, 158, 11, 0.14)';
                    pillColor = '#b45309';
                  } else if (statusKind === 'insufficient_history') {
                    pillText = `Insufficient history (${filter.min_history_days || '?'}d)`;
                    pillBg = 'rgba(245, 158, 11, 0.14)';
                    pillColor = '#b45309';
                    showRetry = Boolean(isChecked);
                  } else if (hasData && statusKind === 'partial' && eligTotal > 0) {
                    pillText = `Partial (${nonNull}/${eligTotal})`;
                    pillBg = 'rgba(16, 185, 129, 0.12)';
                    pillColor = '#047857';
                  } else if (!hasData) {
                    pillText = formatMissingFeedReason(filter.feeds);
                  }

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
                      {pillText && (
                        <span
                          title={bCov?.status_reason || pillText}
                          style={{
                            fontSize: '10px',
                            color: pillColor,
                            background: pillBg,
                            padding: '2px 6px',
                            borderRadius: '3px',
                            whiteSpace: 'nowrap',
                          }}
                        >
                          {pillText}
                        </span>
                      )}
                      {showRetry && onRetryFilter && (
                        <button
                          type="button"
                          onClick={e => {
                            e.preventDefault();
                            e.stopPropagation();
                            onRetryFilter(filter.id);
                          }}
                          style={{
                            fontSize: '10px',
                            padding: '2px 6px',
                            borderRadius: '3px',
                            border: '1px solid var(--border)',
                            background: 'var(--panel-bg)',
                            color: 'var(--link-teal)',
                            cursor: 'pointer',
                          }}
                        >
                          Retry
                        </button>
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
