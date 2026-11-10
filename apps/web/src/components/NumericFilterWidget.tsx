import React, { useState } from 'react';
import { DataEnsureJob, FilterBackendStatus, FilterDefinition } from '../types';
import { DualRangeSlider } from './DualRangeSlider';
import { ChevronDown, ChevronUp } from 'lucide-react';
import { round2 } from '../utils/formatters';

interface NumericFilterWidgetProps {
  filter: FilterDefinition;
  isOpen: boolean;
  onToggleOpen: () => void;
  currentMin: number | null;
  currentMax: number | null;
  values: number[];
  onFilterChange: (min: number | null, max: number | null) => void;
  onRemove: () => void;
  isRemovable: boolean;
  filterStatus?: FilterBackendStatus;
  activeJob?: DataEnsureJob;
  isChecking?: boolean;
  onRetrySync?: (fid: string) => void;
}

export const NumericFilterWidget: React.FC<NumericFilterWidgetProps> = ({
  filter,
  isOpen,
  onToggleOpen,
  currentMin,
  currentMax,
  values,
  onFilterChange,
  onRemove,
  isRemovable,
  filterStatus,
  activeJob,
  isChecking,
  onRetrySync,
}) => {
  const [isHovered, setIsHovered] = useState(false);

  // Compute actual min and max bounds from values
  const hasData = values.length > 0;
  const minBound = hasData ? Math.min(...values) : 0;
  const maxBound = hasData ? Math.max(...values) : 100;

  const activeMin = currentMin ?? minBound;
  const activeMax = currentMax ?? maxBound;
  const isApplied = currentMin !== null || currentMax !== null;

  // Handle Preset Clicks
  const handlePreset = (index: number) => {
    if (!hasData) return;
    const sorted = [...values].sort((a, b) => a - b);
    const n = sorted.length;
    const q = (p: number) => sorted[Math.min(n - 1, Math.floor(p * n))];

    if (filter.id === 'market_cap' && n >= 251) {
      const reversed = [...sorted].reverse();
      // Large (0..99), Mid (100..249), Small (250+)
      const presets: [number | null, number | null][] = [
        [null, reversed[250]], // Smallcap
        [reversed[249], reversed[100]], // Midcap
        [reversed[99], null], // Largecap
      ];
      onFilterChange(presets[index][0], presets[index][1]);
    } else {
      // Tertiles: Low (0..33%), Mid (33%..67%), High (67%..100%)
      const presets: [number, number][] = [
        [sorted[0], q(0.333)],
        [q(0.333), q(0.667)],
        [q(0.667), sorted[n - 1]],
      ];
      onFilterChange(presets[index][0], presets[index][1]);
    }
  };

  const presetLabels =
    filter.id === 'market_cap'
      ? ['Smallcap', 'Midcap', 'Largecap']
      : ['Low', 'Mid', 'High'];

  return (
    <div
      className="filter-section"
      onMouseEnter={() => setIsHovered(true)}
      onMouseLeave={() => setIsHovered(false)}
    >
      <div className="filter-section-header" onClick={onToggleOpen}>
        <span>
          {filter.id === 'market_cap'
            ? 'Market Cap'
            : filter.id === 'close_price'
            ? 'Close Price (Rs)'
            : filter.unit && !filter.name.includes('%')
            ? `${filter.name} (${filter.unit})`
            : filter.name}
          {isApplied && <span className="filter-applied-dot">•</span>}
        </span>
        <div className="filter-section-actions" onClick={e => e.stopPropagation()}>
          {(isHovered || isRemovable) && isRemovable && (
            <span
              className="filter-remove-link"
              onClick={e => {
                e.stopPropagation();
                onRemove();
              }}
            >
              Remove
            </span>
          )}
          <span className="cursor-pointer" onClick={onToggleOpen}>
            {isOpen ? <ChevronUp size={16} /> : <ChevronDown size={16} />}
          </span>
        </div>
      </div>

      {isOpen && (
        <div className="filter-section-body">
          {!hasData ? (
            <div style={{ color: 'var(--text-muted)', fontSize: '12px', display: 'flex', flexDirection: 'column', gap: '6px' }}>
              <span>
                {isChecking || activeJob?.status === 'queued' || activeJob?.status === 'running' || filterStatus?.status === 'queued' || filterStatus?.status === 'running'
                  ? `Syncing ${filter.name}... ${activeJob?.message || filterStatus?.status_reason || ''}`
                  : activeJob?.status === 'blocked' || filterStatus?.status === 'blocked'
                    ? (activeJob?.error || filterStatus?.status_reason || 'Rate-limited by NSE host; retry later or drop official files into data/inbox/.')
                    : filterStatus?.status === 'unavailable' || filter.feeds === 'unavailable'
                      ? 'Unavailable from public official sources (requires commercial consensus vendor).'
                      : (filterStatus?.status_reason || `Pending data from ${filter.primary_source || 'official source'}.`)}
              </span>
              {onRetrySync && filter.feeds !== 'unavailable' && filterStatus?.status !== 'not_applicable' && (
                <button
                  type="button"
                  onClick={() => onRetrySync(filter.id)}
                  style={{
                    alignSelf: 'flex-start',
                    fontSize: '11px',
                    padding: '3px 8px',
                    borderRadius: '4px',
                    border: '1px solid var(--border)',
                    background: 'var(--panel-secondary)',
                    color: 'var(--link-teal)',
                    cursor: 'pointer',
                  }}
                >
                  {activeJob?.status === 'running' || activeJob?.status === 'queued' ? 'Sync running...' : 'Sync / Retry'}
                </button>
              )}
            </div>
          ) : (
            <>
              <DualRangeSlider
                minBound={minBound}
                maxBound={maxBound}
                currentMin={activeMin}
                currentMax={activeMax}
                onChange={(min, max) => onFilterChange(min, max)}
              />

              <div className="filter-input-row">
                <input
                  type="text"
                  value={round2(activeMin)}
                  onChange={e => {
                    const v = e.target.value.trim().replace(/,/g, '');
                    const n = v === '' || isNaN(Number(v)) ? null : Number(v);
                    onFilterChange(n, currentMax);
                  }}
                />
                <span className="filter-input-to">to</span>
                <input
                  type="text"
                  value={round2(activeMax)}
                  onChange={e => {
                    const v = e.target.value.trim().replace(/,/g, '');
                    const n = v === '' || isNaN(Number(v)) ? null : Number(v);
                    onFilterChange(currentMin, n);
                  }}
                />
              </div>

              <div className="preset-button-group">
                {presetLabels.map((lbl, idx) => (
                  <button key={lbl} onClick={() => handlePreset(idx)}>
                    {lbl}
                  </button>
                ))}
              </div>
            </>
          )}
        </div>
      )}
    </div>
  );
};
