import React, { useState } from 'react';
import { FilterDefinition, StockRow } from '../types';
import { compileCustomFilter, slugify } from '../utils/compiler';
import { formatIndianNumber } from '../utils/formatters';
import { X, CheckCircle, AlertCircle, Copy } from 'lucide-react';

interface CustomFilterModalProps {
  isOpen: boolean;
  onClose: () => void;
  filterMap: Map<string, FilterDefinition>;
  sampleRows: StockRow[];
  onSaveFilter: (name: string, formula: string, fn: (r: StockRow) => number | null) => void;
}

export const CustomFilterModal: React.FC<CustomFilterModalProps> = ({
  isOpen,
  onClose,
  filterMap,
  sampleRows,
  onSaveFilter,
}) => {
  const [filterName, setFilterName] = useState('');
  const [formula, setFormula] = useState('');
  const [statusMessage, setStatusMessage] = useState<{ text: string; isError: boolean } | null>(null);

  if (!isOpen) return null;

  const handleVerify = () => {
    try {
      const { fn } = compileCustomFilter(formula, filterMap);
      const preview = sampleRows.slice(0, 3).map(r => {
        const val = fn(r);
        return `${r.name.split(' ')[0]}: ${formatIndianNumber(val)}`;
      });
      setStatusMessage({
        text: `Formula valid. Sample outputs: ${preview.join(', ')}`,
        isError: false,
      });
    } catch (err: any) {
      setStatusMessage({
        text: err.message || 'Validation failed',
        isError: true,
      });
    }
  };

  const handleSave = () => {
    const trimmedName = filterName.trim();
    if (!trimmedName) {
      setStatusMessage({ text: 'Please provide a filter name', isError: true });
      return;
    }

    try {
      const { fn } = compileCustomFilter(formula, filterMap);
      onSaveFilter(trimmedName, formula, fn);
      onClose();
    } catch (err: any) {
      setStatusMessage({ text: err.message || 'Save failed', isError: true });
    }
  };

  const handleCopyHeaders = () => {
    const headers = ['Name', 'Sub-Sector', 'Sector', ...Array.from(filterMap.values()).map(f => f.name)];
    navigator.clipboard.writeText(headers.join('\t'));
    setStatusMessage({
      text: 'Template headers copied to clipboard! Paste into row 1 of your spreadsheet.',
      isError: false,
    });
  };

  return (
    <div className="center-modal-backdrop" onClick={onClose}>
      <div className="center-modal-card" onClick={e => e.stopPropagation()}>
        <div className="center-modal-header">
          <div>
            <h3 style={{ fontSize: '16px', fontWeight: 600 }}>Custom Filter Builder</h3>
            <div style={{ fontSize: '12px', color: 'var(--text-secondary)', marginTop: '2px' }}>
              Combine 2 to 5 data items with basic arithmetic (+, -, *, /)
            </div>
          </div>
          <button className="btn-outline" style={{ border: 'none' }} onClick={onClose}>
            <X size={18} />
          </button>
        </div>

        <div className="center-modal-body">
          <div style={{ marginBottom: '14px' }}>
            <label style={{ display: 'block', fontSize: '12px', fontWeight: 600, marginBottom: '6px' }}>
              Filter Name
            </label>
            <input
              type="text"
              placeholder="e.g. Quick Ratio Custom"
              value={filterName}
              onChange={e => setFilterName(e.target.value)}
              style={{ width: '100%' }}
            />
          </div>

          <div style={{ marginBottom: '14px' }}>
            <label style={{ display: 'block', fontSize: '12px', fontWeight: 600, marginBottom: '6px' }}>
              Formula Expression
            </label>
            <div style={{ fontSize: '12px', color: 'var(--text-secondary)', marginBottom: '6px' }}>
              Wrap each metric name in brackets, e.g.:
              <code style={{ background: 'var(--panel-secondary)', padding: '2px 4px', borderRadius: '3px' }}>
                ([Total Current Assets] - [Total Inventory]) / [Total Current Liabilities]
              </code>
            </div>
            <textarea
              rows={4}
              value={formula}
              onChange={e => setFormula(e.target.value)}
              placeholder="([Market Cap] / [Close Price]) * 100"
              style={{
                width: '100%',
                padding: '8px 10px',
                fontFamily: 'monospace',
                fontSize: '13px',
                border: '1px solid var(--border)',
                borderRadius: '4px',
                background: 'var(--bg)',
                color: 'var(--text-primary)',
              }}
            />
          </div>

          {statusMessage && (
            <div
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: '8px',
                padding: '10px 12px',
                borderRadius: '4px',
                fontSize: '12px',
                marginBottom: '14px',
                background: statusMessage.isError ? '#fee2e2' : '#ecfdf5',
                color: statusMessage.isError ? '#991b1b' : '#065f46',
                border: `1px solid ${statusMessage.isError ? '#fecaca' : '#a7f3d0'}`,
              }}
            >
              {statusMessage.isError ? <AlertCircle size={16} /> : <CheckCircle size={16} />}
              <span>{statusMessage.text}</span>
            </div>
          )}

          <div style={{ display: 'flex', gap: '8px' }}>
            <button className="btn-outline" onClick={handleVerify}>
              Verify
            </button>
            <button className="btn-outline" onClick={handleCopyHeaders}>
              <Copy size={14} /> Copy template headers
            </button>
          </div>
        </div>

        <div className="center-modal-footer">
          <button className="btn-outline" onClick={onClose}>
            Cancel
          </button>
          <button className="btn-primary" onClick={handleSave}>
            Save Filter
          </button>
        </div>
      </div>
    </div>
  );
};
