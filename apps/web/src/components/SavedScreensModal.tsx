import React, { useState } from 'react';
import { SavedScreen, FilterState } from '../types';
import { X, Download, Upload, Copy, Trash2, Check } from 'lucide-react';

interface SavedScreensModalProps {
  isOpen: boolean;
  onClose: () => void;
  savedScreens: SavedScreen[];
  currentNote: string;
  currentFilters: FilterState[];
  currentColumns: string[];
  currentSort: { id: string; dir: 1 | -1 };
  onLoadScreen: (screen: SavedScreen) => void;
  onSaveCurrentScreen: (name: string, note: string) => void;
  onDeleteScreen: (id: string) => void;
}

export const PREBUILT_SCREENS: Omit<SavedScreen, 'id' | 'createdAt'>[] = [
  {
    name: 'High ROE + Low PE',
    note: 'Quality compounders trading at attractive valuations',
    filters: [
      { id: 'return_on_equity', min: 15, max: null },
      { id: 'pe_ratio', min: 0, max: 25 },
    ],
    columns: ['market_cap', 'close_price', 'pe_ratio', 'return_on_equity', '1m_return'],
    sort: { id: 'return_on_equity', dir: -1 },
  },
  {
    name: 'Low-Debt Midcaps',
    note: 'Midcap companies with healthy balance sheets and low leverage',
    filters: [
      { id: 'debt_to_equity', min: null, max: 0.5 },
      { id: 'current_ratio', min: 1.5, max: null },
    ],
    columns: ['market_cap', 'close_price', 'pe_ratio', '1m_return', '1d_return'],
    sort: { id: 'market_cap', dir: -1 },
  },
  {
    name: 'High Dividend Yield',
    note: 'Established dividend payers with solid yield',
    filters: [{ id: 'dividend_yield', min: 3, max: null }],
    columns: ['market_cap', 'close_price', 'dividend_yield', 'pe_ratio'],
    sort: { id: 'dividend_yield', dir: -1 },
  },
  {
    name: 'Strong Momentum',
    note: 'Outperforming stocks with strong 1M and 1Y momentum',
    filters: [
      { id: '1m_return', min: 5, max: null },
      { id: '1y_return', min: 20, max: null },
    ],
    columns: ['market_cap', 'close_price', '1m_return', '1y_return', 'pe_ratio'],
    sort: { id: '1m_return', dir: -1 },
  },
];

export const SavedScreensModal: React.FC<SavedScreensModalProps> = ({
  isOpen,
  onClose,
  savedScreens,
  currentNote,
  currentFilters,
  currentColumns,
  currentSort,
  onLoadScreen,
  onSaveCurrentScreen,
  onDeleteScreen,
}) => {
  const [screenName, setScreenName] = useState('');
  const [copyFeedback, setCopyFeedback] = useState<string | null>(null);

  if (!isOpen) return null;

  const handleSave = () => {
    const name = screenName.trim() || `Screen ${savedScreens.length + 1}`;
    onSaveCurrentScreen(name, currentNote);
    setScreenName('');
  };

  const handleExportJson = (screen?: SavedScreen) => {
    const targetScreen = screen || {
      id: 'current',
      name: screenName || 'Current Screen',
      note: currentNote,
      filters: currentFilters,
      columns: currentColumns,
      sort: currentSort,
      createdAt: new Date().toISOString(),
    };

    const dataStr = 'data:text/json;charset=utf-8,' + encodeURIComponent(JSON.stringify(targetScreen, null, 2));
    const dlAnchor = document.createElement('a');
    dlAnchor.setAttribute('href', dataStr);
    dlAnchor.setAttribute('download', `${targetScreen.name.toLowerCase().replace(/\s+/g, '_')}.json`);
    dlAnchor.click();
  };

  const handleCopyJson = () => {
    const payload = {
      note: currentNote,
      filters: currentFilters,
      columns: currentColumns,
      sort: currentSort,
    };
    navigator.clipboard.writeText(JSON.stringify(payload, null, 2));
    setCopyFeedback('Screen JSON copied to clipboard!');
    setTimeout(() => setCopyFeedback(null), 2500);
  };

  const handleImportJson = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;

    const reader = new FileReader();
    reader.onload = event => {
      try {
        const parsed = JSON.parse(event.target?.result as string);
        if (parsed.filters && parsed.columns) {
          onLoadScreen({
            id: 'imported_' + Date.now(),
            name: parsed.name || file.name.replace(/\.json$/i, ''),
            note: parsed.note || '',
            filters: parsed.filters,
            columns: parsed.columns,
            sort: parsed.sort || { id: 'market_cap', dir: -1 },
            createdAt: new Date().toISOString(),
          });
          onClose();
        }
      } catch (err) {
        alert('Invalid screen JSON file format');
      }
    };
    reader.readAsText(file);
    e.target.value = '';
  };

  return (
    <div className="center-modal-backdrop" onClick={onClose}>
      <div className="center-modal-card" onClick={e => e.stopPropagation()} style={{ width: '680px' }}>
        <div className="center-modal-header">
          <div>
            <h3 style={{ fontSize: '16px', fontWeight: 600 }}>Saved Screens & Sharing</h3>
            <div style={{ fontSize: '12px', color: 'var(--text-secondary)', marginTop: '2px' }}>
              Save, load, export, and import screen configurations
            </div>
          </div>
          <button className="btn-outline" style={{ border: 'none' }} onClick={onClose}>
            <X size={18} />
          </button>
        </div>

        <div className="center-modal-body">
          {/* Save Current Screen Form */}
          <div
            style={{
              padding: '12px 14px',
              background: 'var(--panel-secondary)',
              borderRadius: '6px',
              border: '1px solid var(--border)',
              marginBottom: '16px',
            }}
          >
            <div style={{ fontWeight: 600, fontSize: '13px', marginBottom: '8px' }}>
              Save Current Screen
            </div>
            <div style={{ display: 'flex', gap: '8px' }}>
              <input
                type="text"
                placeholder="Give your screen a name..."
                value={screenName}
                onChange={e => setScreenName(e.target.value)}
                style={{ flex: 1 }}
              />
              <button className="btn-primary" onClick={handleSave}>
                Save Screen
              </button>
            </div>
          </div>

          {/* Quick Share / Export Tools */}
          <div style={{ display: 'flex', gap: '8px', marginBottom: '16px' }}>
            <button className="btn-outline" onClick={handleCopyJson}>
              <Copy size={14} /> Copy Screen as JSON
            </button>
            <button className="btn-outline" onClick={() => handleExportJson()}>
              <Download size={14} /> Download JSON
            </button>
            <label className="btn-outline" style={{ cursor: 'pointer', margin: 0 }}>
              <Upload size={14} /> Import Screen JSON
              <input type="file" accept=".json" onChange={handleImportJson} style={{ display: 'none' }} />
            </label>
          </div>

          {copyFeedback && (
            <div
              style={{
                fontSize: '12px',
                color: '#16a34a',
                display: 'flex',
                alignItems: 'center',
                gap: '6px',
                marginBottom: '12px',
              }}
            >
              <Check size={14} /> {copyFeedback}
            </div>
          )}

          {/* User's Saved Screens */}
          <div style={{ marginBottom: '16px' }}>
            <h4 style={{ fontSize: '13px', fontWeight: 600, marginBottom: '8px' }}>
              Your Saved Screens ({savedScreens.length})
            </h4>
            {savedScreens.length === 0 ? (
              <div style={{ fontSize: '12px', color: 'var(--text-muted)' }}>
                No saved screens yet. Save your current screen above!
              </div>
            ) : (
              <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
                {savedScreens.map(s => (
                  <div
                    key={s.id}
                    style={{
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'space-between',
                      padding: '10px 12px',
                      border: '1px solid var(--border)',
                      borderRadius: '4px',
                      background: 'var(--bg)',
                    }}
                  >
                    <div>
                      <div style={{ fontWeight: 600, fontSize: '13px' }}>{s.name}</div>
                      {s.note && <div style={{ fontSize: '12px', color: 'var(--text-secondary)' }}>{s.note}</div>}
                    </div>
                    <div style={{ display: 'flex', gap: '6px' }}>
                      <button
                        className="btn-outline"
                        style={{ padding: '4px 8px', fontSize: '12px' }}
                        onClick={() => {
                          onLoadScreen(s);
                          onClose();
                        }}
                      >
                        Load
                      </button>
                      <button
                        className="btn-outline"
                        style={{ padding: '4px 8px', fontSize: '12px' }}
                        onClick={() => handleExportJson(s)}
                        title="Download JSON"
                      >
                        <Download size={13} />
                      </button>
                      <button
                        className="btn-outline"
                        style={{ padding: '4px 8px', fontSize: '12px', color: '#ef4444' }}
                        onClick={() => onDeleteScreen(s.id)}
                        title="Delete"
                      >
                        <Trash2 size={13} />
                      </button>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>

          {/* Built-in Pre-Built Screens Catalog */}
          <div>
            <h4 style={{ fontSize: '13px', fontWeight: 600, marginBottom: '8px' }}>
              Pre-Built Screens
            </h4>
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '8px' }}>
              {PREBUILT_SCREENS.map(pre => (
                <div
                  key={pre.name}
                  style={{
                    padding: '10px 12px',
                    border: '1px solid var(--border)',
                    borderRadius: '4px',
                    background: 'var(--panel-secondary)',
                    display: 'flex',
                    flexDirection: 'column',
                    justifyContent: 'space-between',
                  }}
                >
                  <div>
                    <div style={{ fontWeight: 600, fontSize: '13px' }}>{pre.name}</div>
                    <div style={{ fontSize: '11px', color: 'var(--text-secondary)', marginTop: '2px' }}>
                      {pre.note}
                    </div>
                  </div>
                  <button
                    className="btn-outline"
                    style={{ alignSelf: 'flex-start', marginTop: '8px', fontSize: '11px', padding: '3px 8px' }}
                    onClick={() => {
                      onLoadScreen({
                        ...pre,
                        id: 'pre_' + pre.name.toLowerCase().replace(/\s+/g, '_'),
                        createdAt: new Date().toISOString(),
                      });
                      onClose();
                    }}
                  >
                    Load Screen
                  </button>
                </div>
              ))}
            </div>
          </div>
        </div>

        <div className="center-modal-footer">
          <button className="btn-primary" onClick={onClose}>
            Done
          </button>
        </div>
      </div>
    </div>
  );
};
