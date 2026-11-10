import React, { useState } from 'react';
import { StockRow, FilterDefinition } from '../types';
import { formatIndianNumber } from '../utils/formatters';
import { X, Info } from 'lucide-react';

interface StockDetailDrawerProps {
  stock: StockRow | null;
  onClose: () => void;
  filterMap: Map<string, FilterDefinition>;
}

const QUANT_METRICS = [
  { id: 'fundamental_score', label: 'Fundamental Score (1-10)', weight: 'Val 25% · Prof 30% · Growth 25% · Health 20%' },
  { id: 'price_momentum_rank', label: 'Price Momentum Rank', weight: '60% Abs 12M Return + 40% Rel Sub-sector Return' },
  { id: 'earnings_quality_rank', label: 'Earnings Quality Rank', weight: 'Equal mix: Net Margin + Asset Turnover + CFO/NI' },
  { id: 'price_to_intrinsic_value_rank', label: 'Price to Intrinsic Value Rank', weight: 'Median(Graham EPS, FCF Perpetuity, Div Gordon)' },
  { id: 'value_momentum_rank', label: 'Value Momentum Rank', weight: '50% Growth-Adj PE + 50% Price Momentum' },
];

const UNAVAILABLE_METRICS = [
  { name: 'Forward PE / Forward PS', reason: 'Requires commercial sell-side consensus' },
  { name: '1Y Forward Growth (Rev/EPS/EBITDA/CFO)', reason: 'Requires commercial forward estimates' },
  { name: 'Analyst Ratings & Target Upside', reason: 'Proprietary broker research (import via Excel)' },
];

export const StockDetailDrawer: React.FC<StockDetailDrawerProps> = ({
  stock,
  onClose,
  filterMap,
}) => {
  const [showScoreInfo, setShowScoreInfo] = useState(false);

  if (!stock) return null;

  const keyMetrics = [
    { id: 'market_cap', label: 'Market Cap (Rs Cr)', src: 'NSE Bhavcopy x Shares' },
    { id: 'close_price', label: 'Close Price (Rs)', src: 'Official Exchange Bhavcopy' },
    { id: 'pe_ratio', label: 'PE Ratio', src: 'Close / EPS (FY0)' },
    { id: 'pb_ratio', label: 'PB Ratio', src: 'Close / BVPS' },
    { id: '1m_return', label: '1M Return (%)', src: 'Adjusted EOD Series' },
    { id: '1d_return', label: '1D Return (%)', src: 'Bhavcopy Daily Change' },
    { id: 'return_on_equity', label: 'Return on Equity (%)', src: 'Ind-AS XBRL Filing' },
    { id: 'pe_premium_vs_sector', label: 'PE Prem vs Sector (%)', src: 'Market-wide Benchmark' },
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
        <h4 style={{ fontSize: '13px', fontWeight: 600, marginBottom: '10px' }}>
          Key Metrics (with Source Traceability)
        </h4>

        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '8px', marginBottom: '18px' }}>
          {keyMetrics.map(m => {
            const val = stock.v[m.id];
            const def = filterMap.get(m.id);
            return (
              <div
                key={m.id}
                title={`Formula: ${def?.formula || m.label}\nSource: ${m.src}\nNull rule: ${def?.null_rule || 'Standard'}`}
                style={{
                  background: 'var(--panel-secondary)',
                  padding: '9px 10px',
                  borderRadius: '6px',
                  border: '1px solid var(--border-light)',
                }}
              >
                <div style={{ fontSize: '11px', color: 'var(--text-secondary)', marginBottom: '3px' }}>
                  {m.label}
                </div>
                <div style={{ fontSize: '14px', fontWeight: 600, color: 'var(--text-primary)' }}>
                  {val === null || val === undefined ? '—' : formatIndianNumber(val)}
                </div>
                <div style={{ fontSize: '10px', color: 'var(--text-muted)', marginTop: '2px' }}>
                  {m.src}
                </div>
              </div>
            );
          })}
        </div>

        {/* Quant Scores Section */}
        <div style={{ borderTop: '1px solid var(--border)', paddingTop: '14px', marginBottom: '16px' }}>
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '8px' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
              <h4 style={{ fontSize: '13px', fontWeight: 600 }}>Quant Special Ranks</h4>
              <span
                style={{
                  fontSize: '10px',
                  background: 'rgba(245, 158, 11, 0.14)',
                  color: '#b45309',
                  padding: '2px 6px',
                  borderRadius: '3px',
                  fontWeight: 600,
                }}
              >
                Approximate - computed locally
              </span>
            </div>
            <button
              type="button"
              className="btn-outline"
              style={{ border: 'none', padding: '2px 4px' }}
              title="View local quant score weights (config/scores.yaml)"
              onClick={() => setShowScoreInfo(!showScoreInfo)}
            >
              <Info size={14} />
            </button>
          </div>

          {showScoreInfo && (
            <div
              style={{
                fontSize: '11px',
                background: 'var(--panel-secondary)',
                padding: '8px 10px',
                borderRadius: '4px',
                border: '1px solid var(--border)',
                marginBottom: '10px',
                color: 'var(--text-secondary)',
              }}
            >
              Computed strictly across full listed market percentiles (`config/scores.yaml`). Never claims parity with external platforms.
            </div>
          )}

          <div style={{ display: 'flex', flexDirection: 'column', gap: '6px' }}>
            {QUANT_METRICS.map(qm => {
              const qVal = stock.v[qm.id];
              return (
                <div
                  key={qm.id}
                  title={qm.weight}
                  style={{
                    display: 'flex',
                    justifyContent: 'space-between',
                    alignItems: 'center',
                    fontSize: '12px',
                    padding: '6px 8px',
                    background: 'var(--panel-secondary)',
                    borderRadius: '4px',
                  }}
                >
                  <span style={{ color: 'var(--text-secondary)' }}>{qm.label}</span>
                  <span style={{ fontWeight: 600 }}>
                    {qVal !== null && qVal !== undefined ? formatIndianNumber(qVal) : '—'}
                  </span>
                </div>
              );
            })}
          </div>
        </div>

        {/* Unavailable Notice Section */}
        <div style={{ borderTop: '1px solid var(--border)', paddingTop: '14px', marginBottom: '16px' }}>
          <h4 style={{ fontSize: '13px', fontWeight: 600, marginBottom: '8px' }}>
            Not Available From Official Sources
          </h4>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '6px' }}>
            {UNAVAILABLE_METRICS.map(u => (
              <div
                key={u.name}
                style={{
                  fontSize: '11px',
                  padding: '6px 8px',
                  background: 'var(--tag-bg)',
                  borderRadius: '4px',
                  color: 'var(--text-secondary)',
                }}
              >
                <div style={{ fontWeight: 600 }}>{u.name}</div>
                <div style={{ color: 'var(--text-muted)' }}>{u.reason}</div>
              </div>
            ))}
          </div>
        </div>

        <div style={{ borderTop: '1px solid var(--border)', paddingTop: '14px' }}>
          <h4 style={{ fontSize: '13px', fontWeight: 600, marginBottom: '8px' }}>
            Security Master Provenance
          </h4>
          <div style={{ fontSize: '12px', color: 'var(--text-secondary)', display: 'flex', flexDirection: 'column', gap: '5px' }}>
            <div>Sector: <b style={{ color: 'var(--text-primary)' }}>{stock.sector}</b></div>
            <div>Sub-Sector: <b style={{ color: 'var(--text-primary)' }}>{stock.sub}</b></div>
            <div>Listing Status: <span style={{ color: '#16a34a', fontWeight: 600 }}>Active</span></div>
            <div>Data Policy: Official sources only (NSE / BSE / AMFI / FBIL / SEBI)</div>
          </div>
        </div>
      </div>
    </div>
  );
};
