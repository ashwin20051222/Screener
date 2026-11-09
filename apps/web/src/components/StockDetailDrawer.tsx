import React from 'react';
import { StockRow, FilterDefinition } from '../types';
import { formatIndianNumber } from '../utils/formatters';
import { X, ExternalLink } from 'lucide-react';

interface StockDetailDrawerProps {
  stock: StockRow | null;
  onClose: () => void;
  filterMap: Map<string, FilterDefinition>;
}

export const StockDetailDrawer: React.FC<StockDetailDrawerProps> = ({
  stock,
  onClose,
  filterMap,
}) => {
  if (!stock) return null;

  const keyMetrics = [
    { id: 'market_cap', label: 'Market Cap (Rs Cr)' },
    { id: 'close_price', label: 'Close Price (Rs)' },
    { id: 'pe_ratio', label: 'PE Ratio' },
    { id: '1m_return', label: '1M Return (%)' },
    { id: '1d_return', label: '1D Return (%)' },
    { id: 'return_on_equity', label: 'Return on Equity (%)' },
  ];

  return (
    <div className="stock-drawer-overlay">
      <div className="drawer-header">
        <div>
          <h2 style={{ fontSize: '16px', fontWeight: 600, color: 'var(--text-primary)' }}>
            {stock.name}
          </h2>
          <div style={{ fontSize: '12px', color: 'var(--text-secondary)', marginTop: '2px' }}>
            {stock.sub} • {stock.sector}
          </div>
        </div>
        <button className="btn-outline" style={{ border: 'none' }} onClick={onClose}>
          <X size={18} />
        </button>
      </div>

      <div className="drawer-body">
        <h4 style={{ fontSize: '13px', fontWeight: 600, marginBottom: '12px' }}>
          Key Metrics
        </h4>

        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '10px', marginBottom: '20px' }}>
          {keyMetrics.map(m => {
            const val = stock.v[m.id];
            return (
              <div
                key={m.id}
                style={{
                  background: 'var(--panel-secondary)',
                  padding: '10px',
                  borderRadius: '6px',
                  border: '1px solid var(--border-light)',
                }}
              >
                <div style={{ fontSize: '11px', color: 'var(--text-secondary)', marginBottom: '4px' }}>
                  {m.label}
                </div>
                <div style={{ fontSize: '15px', fontWeight: 600, color: 'var(--text-primary)' }}>
                  {formatIndianNumber(val)}
                </div>
              </div>
            );
          })}
        </div>

        <div style={{ borderTop: '1px solid var(--border)', paddingTop: '16px' }}>
          <h4 style={{ fontSize: '13px', fontWeight: 600, marginBottom: '10px' }}>
            Security Master Details
          </h4>
          <div style={{ fontSize: '12px', color: 'var(--text-secondary)', display: 'flex', flexDirection: 'column', gap: '6px' }}>
            <div>Sector: <b style={{ color: 'var(--text-primary)' }}>{stock.sector}</b></div>
            <div>Sub-Sector: <b style={{ color: 'var(--text-primary)' }}>{stock.sub}</b></div>
            <div>Listing Status: <span style={{ color: '#16a34a', fontWeight: 600 }}>Active</span></div>
            <div>Source: Bhavcopy / Official Exchange Master</div>
          </div>
        </div>
      </div>
    </div>
  );
};
