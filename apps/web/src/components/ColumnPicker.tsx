import React from 'react';
import { FilterDefinition } from '../types';

interface ColumnPickerProps {
  isOpen: boolean;
  onClose: () => void;
  availableFilters: FilterDefinition[];
  loadedFilterIds: Set<string>;
  activeColumns: string[];
  onToggleColumn: (id: string, isChecked: boolean) => void;
}

export const ColumnPicker: React.FC<ColumnPickerProps> = ({
  isOpen,
  onClose,
  availableFilters,
  loadedFilterIds,
  activeColumns,
  onToggleColumn,
}) => {
  if (!isOpen) return null;

  // Show only metrics that have data or are known
  const visibleOptions = availableFilters.filter(f => loadedFilterIds.has(f.id));

  return (
    <div className="column-picker-popup" onClick={e => e.stopPropagation()}>
      <div style={{ fontWeight: 600, fontSize: '13px', marginBottom: '8px', color: 'var(--text-primary)' }}>
        Configure Columns
      </div>
      <div style={{ display: 'flex', flexDirection: 'column', gap: '4px' }}>
        {visibleOptions.map(filter => {
          const isChecked = activeColumns.includes(filter.id);
          return (
            <label
              key={filter.id}
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: '8px',
                padding: '4px 0',
                fontSize: '12px',
                cursor: 'pointer',
                color: 'var(--text-primary)',
              }}
            >
              <input
                type="checkbox"
                checked={isChecked}
                onChange={e => onToggleColumn(filter.id, e.target.checked)}
              />
              <span>{filter.name}</span>
            </label>
          );
        })}
      </div>
    </div>
  );
};
