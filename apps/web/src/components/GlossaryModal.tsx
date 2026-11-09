import React from 'react';
import { FilterDefinition } from '../types';
import { X, ExternalLink } from 'lucide-react';

interface GlossaryModalProps {
  isOpen: boolean;
  onClose: () => void;
  category: string;
  filters: FilterDefinition[];
}

export const GlossaryModal: React.FC<GlossaryModalProps> = ({
  isOpen,
  onClose,
  category,
  filters,
}) => {
  if (!isOpen) return null;

  const categoryFilters = filters.filter(f => f.category === category);

  const getBadgeStyle = (status: string) => {
    switch (status) {
      case 'Official-direct':
        return { background: '#dcfce7', color: '#166534', border: '1px solid #bbf7d0' };
      case 'Computed-from-official':
        return { background: '#e0f2fe', color: '#075985', border: '1px solid #bae6fd' };
      case 'Approximate':
        return { background: '#fef3c7', color: '#92400e', border: '1px solid #fde68a' };
      case 'Unavailable':
      default:
        return { background: '#f3f4f6', color: '#4b5563', border: '1px solid #e5e7eb' };
    }
  };

  return (
    <div className="center-modal-backdrop" onClick={onClose}>
      <div className="center-modal-card" onClick={e => e.stopPropagation()}>
        <div className="center-modal-header">
          <div>
            <h3 style={{ fontSize: '16px', fontWeight: 600 }}>
              Glossary: {category === 'Special' ? 'Quant Ranks & Scores' : category}
            </h3>
            <div style={{ fontSize: '12px', color: 'var(--text-secondary)', marginTop: '2px' }}>
              Official formulas, data sources, update cadences, and availability
            </div>
          </div>
          <button className="btn-outline" style={{ border: 'none' }} onClick={onClose}>
            <X size={18} />
          </button>
        </div>

        <div className="center-modal-body">
          {categoryFilters.length === 0 ? (
            <div style={{ padding: '20px', color: 'var(--text-muted)', textAlign: 'center' }}>
              No metrics documented for this category.
            </div>
          ) : (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '14px' }}>
              {categoryFilters.map(filter => (
                <div
                  key={filter.id}
                  style={{
                    border: '1px solid var(--border)',
                    borderRadius: '6px',
                    padding: '12px 14px',
                    background: 'var(--bg)',
                  }}
                >
                  <div
                    style={{
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'space-between',
                      marginBottom: '6px',
                    }}
                  >
                    <span style={{ fontWeight: 600, fontSize: '14px' }}>{filter.name}</span>
                    <span
                      style={{
                        fontSize: '11px',
                        padding: '2px 8px',
                        borderRadius: '12px',
                        fontWeight: 500,
                        ...getBadgeStyle(filter.availability),
                      }}
                    >
                      {filter.availability}
                    </span>
                  </div>

                  {filter.formula && (
                    <div
                      style={{
                        fontFamily: 'monospace',
                        fontSize: '12px',
                        background: 'var(--panel-secondary)',
                        padding: '6px 10px',
                        borderRadius: '4px',
                        marginBottom: '6px',
                        color: 'var(--text-primary)',
                      }}
                    >
                      Formula: {filter.formula}
                    </div>
                  )}

                  <div style={{ fontSize: '12px', color: 'var(--text-secondary)', display: 'flex', gap: '16px' }}>
                    {filter.frequency && <span>Frequency: {filter.frequency}</span>}
                    {filter.unit && <span>Unit: {filter.unit}</span>}
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>

        <div className="center-modal-footer">
          <button className="btn-primary" onClick={onClose}>
            Close
          </button>
        </div>
      </div>
    </div>
  );
};
