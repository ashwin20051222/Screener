import React, { useState } from 'react';
import { AlertTriangle, CheckCircle, HelpCircle, Save, TrendingUp, X } from 'lucide-react';
import { MatchReport, StockUniverse } from '../types';
import {
  CLIENT_MASTER_SECURITIES,
  convertMatchReportToStockRows,
  MasterSecurity,
} from '../utils/matcherClient';

interface MatchReportModalProps {
  isOpen: boolean;
  report: MatchReport | null;
  defaultUniverseName?: string;
  onClose: () => void;
  onSaveUniverse: (universe: StockUniverse) => void;
}

export const MatchReportModal: React.FC<MatchReportModalProps> = ({
  isOpen,
  report,
  defaultUniverseName = 'My Uploaded Portfolio',
  onClose,
  onSaveUniverse,
}) => {
  const [activeTab, setActiveTab] = useState<'matched' | 'ambiguous' | 'unmatched' | 'pnl'>('matched');
  const [universeName, setUniverseName] = useState(defaultUniverseName);
  const [resolvedAmbiguous, setResolvedAmbiguous] = useState<Record<number, MasterSecurity>>({});
  const [manualMatches, setManualMatches] = useState<Record<number, MasterSecurity>>({});

  if (!isOpen || !report) return null;

  const handleResolveAmbiguous = (rowIndex: number, sec: MasterSecurity) => {
    setResolvedAmbiguous((prev) => ({ ...prev, [rowIndex]: sec }));
  };

  const handleManualMatch = (rowIndex: number, sec: MasterSecurity) => {
    setManualMatches((prev) => ({ ...prev, [rowIndex]: sec }));
  };

  const allRowsWithPnl = report.matched.filter(
    (m) => m.pnl && m.pnl.invested_value !== null && m.pnl.current_value !== null
  );
  const totalInvested = allRowsWithPnl.reduce((sum, m) => sum + (m.pnl?.invested_value || 0), 0);
  const totalCurrent = allRowsWithPnl.reduce((sum, m) => sum + (m.pnl?.current_value || 0), 0);
  const totalPnlAmt = totalCurrent - totalInvested;
  const totalPnlPct = totalInvested > 0 ? (totalPnlAmt / totalInvested) * 100 : 0;

  const handleSave = () => {
    const finalRows = convertMatchReportToStockRows(report, resolvedAmbiguous, manualMatches);
    const newUniverse: StockUniverse = {
      id: `custom_${Date.now()}`,
      name: universeName.trim() || 'Custom Universe',
      type: 'custom',
      rows: finalRows,
      totalMarketCount: finalRows.length,
    };
    onSaveUniverse(newUniverse);
    onClose();
  };

  return (
    <div className="center-modal-backdrop" onClick={onClose}>
      <div
        className="center-modal-card"
        style={{ width: 'min(920px, 94vw)', maxHeight: '88vh' }}
        onClick={(e) => e.stopPropagation()}
      >
        <div className="center-modal-header">
          <div>
            <h3 style={{ fontSize: '16px', fontWeight: 600 }}>Security Master Match Report</h3>
            <div style={{ fontSize: '12px', color: 'var(--text-secondary)', marginTop: '2px' }}>
              Checked against official Security Master across ISIN, NSE Symbol, BSE Code, and Names. Never silently drops rows.
            </div>
          </div>
          <button className="btn-outline" style={{ border: 'none' }} onClick={onClose}>
            <X size={18} />
          </button>
        </div>

        {/* Summary Metric Chips */}
        <div
          style={{
            padding: '12px 18px',
            backgroundColor: 'var(--panel-secondary)',
            borderBottom: '1px solid var(--border)',
            display: 'flex',
            gap: '12px',
            alignItems: 'center',
            flexWrap: 'wrap',
          }}
        >
          <span style={{ fontSize: '13px', fontWeight: 600 }}>Total Rows: {report.total_rows}</span>
          <span
            style={{
              display: 'inline-flex',
              alignItems: 'center',
              gap: '5px',
              padding: '3px 10px',
              borderRadius: '999px',
              background: 'rgba(22, 163, 74, 0.12)',
              color: '#16a34a',
              fontSize: '12px',
              fontWeight: 600,
            }}
          >
            <CheckCircle size={13} /> Matched: {report.matched_count}
          </span>
          <span
            style={{
              display: 'inline-flex',
              alignItems: 'center',
              gap: '5px',
              padding: '3px 10px',
              borderRadius: '999px',
              background: 'rgba(245, 158, 11, 0.14)',
              color: '#d97706',
              fontSize: '12px',
              fontWeight: 600,
            }}
          >
            <AlertTriangle size={13} /> Ambiguous: {report.ambiguous_count}
          </span>
          <span
            style={{
              display: 'inline-flex',
              alignItems: 'center',
              gap: '5px',
              padding: '3px 10px',
              borderRadius: '999px',
              background: 'rgba(220, 38, 38, 0.12)',
              color: '#dc2626',
              fontSize: '12px',
              fontWeight: 600,
            }}
          >
            <HelpCircle size={13} /> Unmatched: {report.unmatched_count}
          </span>

          {allRowsWithPnl.length > 0 && (
            <span
              style={{
                marginLeft: 'auto',
                display: 'inline-flex',
                alignItems: 'center',
                gap: '6px',
                fontSize: '12px',
                color: totalPnlAmt >= 0 ? '#16a34a' : '#dc2626',
                fontWeight: 600,
              }}
            >
              <TrendingUp size={14} />
              Portfolio P&L: ₹{totalPnlAmt.toLocaleString('en-IN', { maximumFractionDigits: 0 })} ({totalPnlPct >= 0 ? '+' : ''}{totalPnlPct.toFixed(1)}%)
            </span>
          )}
        </div>

        {/* Tab Bar */}
        <div style={{ display: 'flex', gap: '4px', padding: '8px 18px', borderBottom: '1px solid var(--border)', background: 'var(--bg)' }}>
          {([
            ['matched', `Matched (${report.matched_count})`],
            ['ambiguous', `Ambiguous (${report.ambiguous_count})`],
            ['unmatched', `Unmatched (${report.unmatched_count})`],
            ...(allRowsWithPnl.length > 0 ? [['pnl', `Portfolio P&L (${allRowsWithPnl.length})`]] : []),
          ] as Array<[typeof activeTab, string]>).map(([tid, label]) => (
            <button
              key={tid}
              type="button"
              className={activeTab === tid ? 'btn-primary' : 'btn-outline'}
              style={{ fontSize: '12px', padding: '5px 12px' }}
              onClick={() => setActiveTab(tid)}
            >
              {label}
            </button>
          ))}
        </div>

        {/* Body */}
        <div className="center-modal-body" style={{ display: 'block', padding: '14px 18px' }}>
          {activeTab === 'matched' && (
            <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '12px' }}>
              <thead>
                <tr style={{ background: 'var(--header-bg)', textAlign: 'left', borderBottom: '1px solid var(--border)' }}>
                  <th style={{ padding: '8px' }}>Row</th>
                  <th style={{ padding: '8px' }}>Raw Identifier</th>
                  <th style={{ padding: '8px' }}>Matched Security</th>
                  <th style={{ padding: '8px' }}>Symbol</th>
                  <th style={{ padding: '8px' }}>ISIN</th>
                  <th style={{ padding: '8px' }}>Match Tier</th>
                  <th style={{ padding: '8px', textAlign: 'right' }}>Confidence</th>
                </tr>
              </thead>
              <tbody>
                {report.matched.map((m) => (
                  <tr key={m.row_index} style={{ borderBottom: '1px solid var(--border-light)' }}>
                    <td style={{ padding: '7px 8px', color: 'var(--text-muted)' }}>#{m.row_index + 1}</td>
                    <td style={{ padding: '7px 8px', fontWeight: 500 }}>
                      {String(m.raw_input.Identifier || m.raw_input.Symbol || m.raw_input.name || Object.values(m.raw_input)[0])}
                    </td>
                    <td style={{ padding: '7px 8px' }}>{m.matched_security?.name}</td>
                    <td style={{ padding: '7px 8px' }}><code>{m.matched_security?.nse_symbol}</code></td>
                    <td style={{ padding: '7px 8px', color: 'var(--text-muted)' }}>{m.matched_security?.isin}</td>
                    <td style={{ padding: '7px 8px' }}>
                      <span style={{ background: 'var(--tag-bg)', padding: '2px 6px', borderRadius: '3px', fontSize: '11px' }}>
                        {m.match_tier}
                      </span>
                    </td>
                    <td style={{ padding: '7px 8px', textAlign: 'right', color: '#16a34a', fontWeight: 600 }}>{m.confidence}%</td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}

          {activeTab === 'ambiguous' && (
            <div>
              <p style={{ fontSize: '12px', color: 'var(--text-secondary)', marginBottom: '10px' }}>
                These rows matched multiple securities in the master. Select the intended security for each:
              </p>
              <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '12px' }}>
                <thead>
                  <tr style={{ background: 'var(--header-bg)', textAlign: 'left', borderBottom: '1px solid var(--border)' }}>
                    <th style={{ padding: '8px' }}>Row</th>
                    <th style={{ padding: '8px' }}>Raw Identifier</th>
                    <th style={{ padding: '8px' }}>Candidates</th>
                    <th style={{ padding: '8px' }}>Resolve To</th>
                  </tr>
                </thead>
                <tbody>
                  {report.ambiguous.map((amb) => (
                    <tr key={amb.row_index} style={{ borderBottom: '1px solid var(--border-light)' }}>
                      <td style={{ padding: '8px', color: 'var(--text-muted)' }}>#{amb.row_index + 1}</td>
                      <td style={{ padding: '8px', fontWeight: 600 }}>
                        {String(amb.raw_input.Identifier || Object.values(amb.raw_input)[0])}
                      </td>
                      <td style={{ padding: '8px' }}>
                        {amb.candidates?.map((c) => (
                          <div key={c.isin || c.nse_symbol}>
                            • <b>{c.name}</b> ({c.nse_symbol} · {c.isin})
                          </div>
                        ))}
                      </td>
                      <td style={{ padding: '8px' }}>
                        <select
                          style={{ padding: '5px 8px', borderRadius: '4px', border: '1px solid var(--border)', background: 'var(--bg)', color: 'var(--text-primary)' }}
                          value={resolvedAmbiguous[amb.row_index]?.isin || ''}
                          onChange={(e) => {
                            const chosen = amb.candidates?.find((c) => c.isin === e.target.value);
                            if (chosen) handleResolveAmbiguous(amb.row_index, chosen as MasterSecurity);
                          }}
                        >
                          <option value="">-- Choose Security --</option>
                          {amb.candidates?.map((c) => (
                            <option key={c.isin} value={c.isin}>
                              {c.name} ({c.nse_symbol})
                            </option>
                          ))}
                        </select>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}

          {activeTab === 'unmatched' && (
            <div>
              <p style={{ fontSize: '12px', color: 'var(--text-secondary)', marginBottom: '10px' }}>
                Unmatched records can be mapped manually to a listed security or left excluded:
              </p>
              <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '12px' }}>
                <thead>
                  <tr style={{ background: 'var(--header-bg)', textAlign: 'left', borderBottom: '1px solid var(--border)' }}>
                    <th style={{ padding: '8px' }}>Row</th>
                    <th style={{ padding: '8px' }}>Raw Input</th>
                    <th style={{ padding: '8px' }}>Reason</th>
                    <th style={{ padding: '8px' }}>Manual Fix</th>
                  </tr>
                </thead>
                <tbody>
                  {report.unmatched.map((unm) => (
                    <tr key={unm.row_index} style={{ borderBottom: '1px solid var(--border-light)' }}>
                      <td style={{ padding: '8px', color: 'var(--text-muted)' }}>#{unm.row_index + 1}</td>
                      <td style={{ padding: '8px', fontWeight: 500 }}>
                        {String(unm.raw_input.Identifier || Object.values(unm.raw_input)[0])}
                      </td>
                      <td style={{ padding: '8px', color: 'var(--text-secondary)' }}>{unm.notes}</td>
                      <td style={{ padding: '8px' }}>
                        <select
                          style={{ padding: '5px 8px', borderRadius: '4px', border: '1px solid var(--border)', background: 'var(--bg)', color: 'var(--text-primary)' }}
                          value={manualMatches[unm.row_index]?.isin || ''}
                          onChange={(e) => {
                            const chosen = CLIENT_MASTER_SECURITIES.find((s) => s.isin === e.target.value);
                            if (chosen) handleManualMatch(unm.row_index, chosen);
                          }}
                        >
                          <option value="">-- Exclude --</option>
                          {CLIENT_MASTER_SECURITIES.slice(0, 15).map((s) => (
                            <option key={s.isin} value={s.isin}>
                              {s.name} ({s.nse_symbol})
                            </option>
                          ))}
                        </select>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}

          {activeTab === 'pnl' && (
            <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '12px' }}>
              <thead>
                <tr style={{ background: 'var(--header-bg)', textAlign: 'left', borderBottom: '1px solid var(--border)' }}>
                  <th style={{ padding: '8px' }}>Stock</th>
                  <th style={{ padding: '8px', textAlign: 'right' }}>Qty</th>
                  <th style={{ padding: '8px', textAlign: 'right' }}>Buy Price</th>
                  <th style={{ padding: '8px', textAlign: 'right' }}>Close Price</th>
                  <th style={{ padding: '8px', textAlign: 'right' }}>Invested</th>
                  <th style={{ padding: '8px', textAlign: 'right' }}>Current</th>
                  <th style={{ padding: '8px', textAlign: 'right' }}>P&L (₹)</th>
                  <th style={{ padding: '8px', textAlign: 'right' }}>P&L (%)</th>
                </tr>
              </thead>
              <tbody>
                {allRowsWithPnl.map((m) => {
                  const p = m.pnl!;
                  const sec = m.matched_security!;
                  const profit = (p.pnl_amount || 0) >= 0;
                  return (
                    <tr key={m.row_index} style={{ borderBottom: '1px solid var(--border-light)' }}>
                      <td style={{ padding: '7px 8px' }}><b>{sec.name}</b></td>
                      <td style={{ padding: '7px 8px', textAlign: 'right' }}>{p.quantity}</td>
                      <td style={{ padding: '7px 8px', textAlign: 'right' }}>₹{p.buy_price?.toLocaleString('en-IN')}</td>
                      <td style={{ padding: '7px 8px', textAlign: 'right' }}>₹{sec.close_price.toLocaleString('en-IN')}</td>
                      <td style={{ padding: '7px 8px', textAlign: 'right' }}>₹{p.invested_value?.toLocaleString('en-IN')}</td>
                      <td style={{ padding: '7px 8px', textAlign: 'right' }}>₹{p.current_value?.toLocaleString('en-IN')}</td>
                      <td style={{ padding: '7px 8px', textAlign: 'right', color: profit ? '#16a34a' : '#dc2626', fontWeight: 600 }}>
                        {profit ? '+' : ''}₹{p.pnl_amount?.toLocaleString('en-IN')}
                      </td>
                      <td style={{ padding: '7px 8px', textAlign: 'right', color: profit ? '#16a34a' : '#dc2626', fontWeight: 600 }}>
                        {profit ? '+' : ''}{p.pnl_pct?.toFixed(2)}%
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          )}
        </div>

        <div className="center-modal-footer" style={{ justifyContent: 'space-between' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <span style={{ fontSize: '12px', fontWeight: 600 }}>Save As:</span>
            <input
              type="text"
              value={universeName}
              onChange={(e) => setUniverseName(e.target.value)}
              placeholder="Custom Universe Name"
              style={{ width: '240px' }}
            />
          </div>
          <div style={{ display: 'flex', gap: '8px' }}>
            <button className="btn-outline" onClick={onClose}>Cancel</button>
            <button className="btn-primary" onClick={handleSave}>
              <Save size={14} />
              Save Universe ({report.matched_count + Object.keys(resolvedAmbiguous).length + Object.keys(manualMatches).length} stocks)
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};
