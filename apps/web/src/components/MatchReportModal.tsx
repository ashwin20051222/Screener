import React, { useState } from 'react';
import { AlertTriangle, CheckCircle, HelpCircle, Save, TrendingUp, X } from 'lucide-react';
import { MatchRecord, MatchReport, StockUniverse } from '../types';
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

  // Handle resolving an ambiguous row
  const handleResolveAmbiguous = (rowIndex: number, sec: MasterSecurity) => {
    setResolvedAmbiguous((prev) => ({ ...prev, [rowIndex]: sec }));
  };

  // Handle manually mapping an unmatched row
  const handleManualMatch = (rowIndex: number, sec: MasterSecurity) => {
    setManualMatches((prev) => ({ ...prev, [rowIndex]: sec }));
  };

  // Compute portfolio P&L totals
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
    <div className="modal-overlay" onClick={onClose}>
      <div
        className="modal-container"
        style={{ width: '850px', maxHeight: '92vh', display: 'flex', flexDirection: 'column' }}
        onClick={(e) => e.stopPropagation()}
      >
        {/* Header */}
        <div className="modal-header">
          <div>
            <h2 className="modal-title">Security Master Match Report</h2>
            <div style={{ fontSize: '12px', color: 'var(--text-muted)', marginTop: '2px' }}>
              Checked against official Security Master across ISIN, NSE Symbol, BSE Code, and Names.
            </div>
          </div>
          <button className="modal-close-btn" onClick={onClose}>
            <X size={18} />
          </button>
        </div>

        {/* Summary Metric Chips */}
        <div
          style={{
            padding: '14px 24px',
            backgroundColor: 'var(--bg-active)',
            borderBottom: '1px solid var(--border-color)',
            display: 'flex',
            gap: '16px',
            alignItems: 'center',
          }}
        >
          <div style={{ fontSize: '13px', fontWeight: 600, color: 'var(--text-main)' }}>
            Total Rows: {report.total_rows}
          </div>
          <div
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: '6px',
              padding: '4px 10px',
              borderRadius: '999px',
              background: 'rgba(22, 163, 74, 0.12)',
              color: '#16a34a',
              fontSize: '12px',
              fontWeight: 600,
            }}
          >
            <CheckCircle size={14} />
            Matched: {report.matched_count}
          </div>
          <div
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: '6px',
              padding: '4px 10px',
              borderRadius: '999px',
              background: 'rgba(245, 158, 11, 0.12)',
              color: '#f59e0b',
              fontSize: '12px',
              fontWeight: 600,
            }}
          >
            <AlertTriangle size={14} />
            Ambiguous: {report.ambiguous_count}
          </div>
          <div
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: '6px',
              padding: '4px 10px',
              borderRadius: '999px',
              background: 'rgba(220, 38, 38, 0.12)',
              color: '#dc2626',
              fontSize: '12px',
              fontWeight: 600,
            }}
          >
            <HelpCircle size={14} />
            Unmatched: {report.unmatched_count}
          </div>

          {allRowsWithPnl.length > 0 && (
            <div
              style={{
                marginLeft: 'auto',
                display: 'flex',
                alignItems: 'center',
                gap: '6px',
                fontSize: '12px',
                color: totalPnlAmt >= 0 ? '#16a34a' : '#dc2626',
                fontWeight: 600,
              }}
            >
              <TrendingUp size={14} />
              Portfolio P&L: ₹{totalPnlAmt.toLocaleString('en-IN', { maximumFractionDigits: 0 })} ({totalPnlPct >= 0 ? '+' : ''}{totalPnlPct.toFixed(1)}%)
            </div>
          )}
        </div>

        {/* Tab Navigation */}
        <div style={{ display: 'flex', borderBottom: '1px solid var(--border-color)', padding: '0 24px' }}>
          <button
            type="button"
            className={`glossary-tab-btn ${activeTab === 'matched' ? 'active' : ''}`}
            onClick={() => setActiveTab('matched')}
          >
            Matched ({report.matched_count})
          </button>
          <button
            type="button"
            className={`glossary-tab-btn ${activeTab === 'ambiguous' ? 'active' : ''}`}
            onClick={() => setActiveTab('ambiguous')}
          >
            Ambiguous ({report.ambiguous_count})
          </button>
          <button
            type="button"
            className={`glossary-tab-btn ${activeTab === 'unmatched' ? 'active' : ''}`}
            onClick={() => setActiveTab('unmatched')}
          >
            Unmatched ({report.unmatched_count})
          </button>
          {allRowsWithPnl.length > 0 && (
            <button
              type="button"
              className={`glossary-tab-btn ${activeTab === 'pnl' ? 'active' : ''}`}
              onClick={() => setActiveTab('pnl')}
            >
              Portfolio P&L ({allRowsWithPnl.length})
            </button>
          )}
        </div>

        {/* Tab Content Body */}
        <div className="modal-body" style={{ padding: '16px 24px', flex: 1, overflowY: 'auto' }}>
          {/* TAB 1: Matched */}
          {activeTab === 'matched' && (
            <table className="glossary-table">
              <thead>
                <tr>
                  <th>Row</th>
                  <th>Raw Identifier</th>
                  <th>Matched Security</th>
                  <th>Symbol</th>
                  <th>ISIN</th>
                  <th>Match Tier</th>
                  <th>Confidence</th>
                </tr>
              </thead>
              <tbody>
                {report.matched.map((m) => (
                  <tr key={m.row_index}>
                    <td style={{ color: 'var(--text-muted)' }}>#{m.row_index + 1}</td>
                    <td style={{ fontWeight: 500 }}>
                      {String(m.raw_input.Identifier || m.raw_input.Symbol || m.raw_input.name || Object.values(m.raw_input)[0])}
                    </td>
                    <td>{m.matched_security?.name}</td>
                    <td><code>{m.matched_security?.nse_symbol}</code></td>
                    <td><span style={{ fontSize: '11px', color: 'var(--text-muted)' }}>{m.matched_security?.isin}</span></td>
                    <td>
                      <span className="source-pill" style={{ fontSize: '11px' }}>
                        {m.match_tier}
                      </span>
                    </td>
                    <td style={{ color: '#16a34a', fontWeight: 600 }}>{m.confidence}%</td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}

          {/* TAB 2: Ambiguous (with dropdown to choose candidate) */}
          {activeTab === 'ambiguous' && (
            <div>
              <p style={{ fontSize: '13px', color: 'var(--text-muted)', marginBottom: '12px' }}>
                The following rows matched multiple active securities in the master. Please choose the intended company or share class:
              </p>
              <table className="glossary-table">
                <thead>
                  <tr>
                    <th>Row</th>
                    <th>Raw Identifier</th>
                    <th>Detected Candidates</th>
                    <th>Select Action</th>
                  </tr>
                </thead>
                <tbody>
                  {report.ambiguous.map((amb) => {
                    const isResolved = Boolean(resolvedAmbiguous[amb.row_index]);
                    return (
                      <tr key={amb.row_index} style={{ backgroundColor: isResolved ? 'rgba(22, 163, 74, 0.05)' : undefined }}>
                        <td style={{ color: 'var(--text-muted)' }}>#{amb.row_index + 1}</td>
                        <td style={{ fontWeight: 600 }}>
                          {String(amb.raw_input.Identifier || Object.values(amb.raw_input)[0])}
                        </td>
                        <td>
                          <div style={{ fontSize: '12px' }}>
                            {amb.candidates?.map((c) => (
                              <div key={c.isin || c.nse_symbol} style={{ margin: '2px 0' }}>
                                • <strong>{c.name}</strong> ({c.nse_symbol} - {c.isin})
                              </div>
                            ))}
                          </div>
                        </td>
                        <td>
                          <select
                            style={{
                              padding: '6px 10px',
                              borderRadius: '6px',
                              border: '1px solid var(--border-color)',
                              background: 'var(--bg-card)',
                              color: 'var(--text-main)',
                              fontSize: '12px',
                            }}
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
                    );
                  })}
                </tbody>
              </table>
            </div>
          )}

          {/* TAB 3: Unmatched */}
          {activeTab === 'unmatched' && (
            <div>
              <p style={{ fontSize: '13px', color: 'var(--text-muted)', marginBottom: '12px' }}>
                These records could not be found in the official Security Master. You can map them to a listed company manually or exclude them:
              </p>
              <table className="glossary-table">
                <thead>
                  <tr>
                    <th>Row</th>
                    <th>Raw Input</th>
                    <th>Notes</th>
                    <th>Manual Resolution</th>
                  </tr>
                </thead>
                <tbody>
                  {report.unmatched.map((unm) => (
                    <tr key={unm.row_index}>
                      <td style={{ color: 'var(--text-muted)' }}>#{unm.row_index + 1}</td>
                      <td style={{ fontWeight: 500 }}>
                        {String(unm.raw_input.Identifier || Object.values(unm.raw_input)[0])}
                      </td>
                      <td style={{ fontSize: '12px', color: 'var(--text-muted)' }}>{unm.notes}</td>
                      <td>
                        <select
                          style={{
                            padding: '6px 10px',
                            borderRadius: '6px',
                            border: '1px solid var(--border-color)',
                            background: 'var(--bg-card)',
                            color: 'var(--text-main)',
                            fontSize: '12px',
                          }}
                          value={manualMatches[unm.row_index]?.isin || ''}
                          onChange={(e) => {
                            const chosen = CLIENT_MASTER_SECURITIES.find((s) => s.isin === e.target.value);
                            if (chosen) handleManualMatch(unm.row_index, chosen);
                          }}
                        >
                          <option value="">-- Exclude from Universe --</option>
                          {CLIENT_MASTER_SECURITIES.slice(0, 15).map((s) => (
                            <option key={s.isin} value={s.isin}>
                              Map to: {s.name} ({s.nse_symbol})
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

          {/* TAB 4: Portfolio P&L */}
          {activeTab === 'pnl' && (
            <div>
              <div
                style={{
                  display: 'grid',
                  gridTemplateColumns: 'repeat(4, 1fr)',
                  gap: '12px',
                  marginBottom: '16px',
                }}
              >
                <div className="card" style={{ padding: '12px', textAlign: 'center' }}>
                  <div style={{ fontSize: '11px', color: 'var(--text-muted)' }}>Total Invested</div>
                  <div style={{ fontSize: '16px', fontWeight: 700 }}>₹{totalInvested.toLocaleString('en-IN', { maximumFractionDigits: 0 })}</div>
                </div>
                <div className="card" style={{ padding: '12px', textAlign: 'center' }}>
                  <div style={{ fontSize: '11px', color: 'var(--text-muted)' }}>Current Value</div>
                  <div style={{ fontSize: '16px', fontWeight: 700 }}>₹{totalCurrent.toLocaleString('en-IN', { maximumFractionDigits: 0 })}</div>
                </div>
                <div className="card" style={{ padding: '12px', textAlign: 'center' }}>
                  <div style={{ fontSize: '11px', color: 'var(--text-muted)' }}>Net P&L (₹)</div>
                  <div style={{ fontSize: '16px', fontWeight: 700, color: totalPnlAmt >= 0 ? '#16a34a' : '#dc2626' }}>
                    {totalPnlAmt >= 0 ? '+' : ''}₹{totalPnlAmt.toLocaleString('en-IN', { maximumFractionDigits: 0 })}
                  </div>
                </div>
                <div className="card" style={{ padding: '12px', textAlign: 'center' }}>
                  <div style={{ fontSize: '11px', color: 'var(--text-muted)' }}>Return (%)</div>
                  <div style={{ fontSize: '16px', fontWeight: 700, color: totalPnlPct >= 0 ? '#16a34a' : '#dc2626' }}>
                    {totalPnlPct >= 0 ? '+' : ''}{totalPnlPct.toFixed(2)}%
                  </div>
                </div>
              </div>

              <table className="glossary-table">
                <thead>
                  <tr>
                    <th>Stock</th>
                    <th>Qty</th>
                    <th>Buy Price</th>
                    <th>Close Price</th>
                    <th>Invested</th>
                    <th>Current Value</th>
                    <th>P&L (₹)</th>
                    <th>P&L (%)</th>
                  </tr>
                </thead>
                <tbody>
                  {allRowsWithPnl.map((m) => {
                    const p = m.pnl!;
                    const sec = m.matched_security!;
                    const isProfit = (p.pnl_amount || 0) >= 0;
                    return (
                      <tr key={m.row_index}>
                        <td><strong>{sec.name}</strong></td>
                        <td>{p.quantity}</td>
                        <td>₹{p.buy_price?.toLocaleString('en-IN')}</td>
                        <td>₹{sec.close_price.toLocaleString('en-IN')}</td>
                        <td>₹{p.invested_value?.toLocaleString('en-IN')}</td>
                        <td>₹{p.current_value?.toLocaleString('en-IN')}</td>
                        <td style={{ color: isProfit ? '#16a34a' : '#dc2626', fontWeight: 600 }}>
                          {isProfit ? '+' : ''}₹{p.pnl_amount?.toLocaleString('en-IN')}
                        </td>
                        <td style={{ color: isProfit ? '#16a34a' : '#dc2626', fontWeight: 600 }}>
                          {isProfit ? '+' : ''}{p.pnl_pct?.toFixed(2)}%
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          )}
        </div>

        {/* Footer */}
        <div
          className="modal-footer"
          style={{
            display: 'flex',
            justifyContent: 'space-between',
            alignItems: 'center',
            padding: '16px 24px',
          }}
        >
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <span style={{ fontSize: '13px', fontWeight: 600 }}>Save As:</span>
            <input
              type="text"
              value={universeName}
              onChange={(e) => setUniverseName(e.target.value)}
              placeholder="Custom Universe Name"
              style={{
                padding: '6px 12px',
                borderRadius: '6px',
                border: '1px solid var(--border-color)',
                background: 'var(--bg-card)',
                color: 'var(--text-main)',
                fontSize: '13px',
                width: '260px',
              }}
            />
          </div>

          <div style={{ display: 'flex', gap: '12px' }}>
            <button className="btn-cancel" onClick={onClose}>
              Cancel
            </button>
            <button className="btn-apply" onClick={handleSave}>
              <Save size={14} style={{ marginRight: '6px', verticalAlign: 'middle' }} />
              Save Universe ({report.matched_count + Object.keys(resolvedAmbiguous).length + Object.keys(manualMatches).length} stocks)
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};
