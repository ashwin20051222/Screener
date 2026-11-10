import React, { useRef, useState } from 'react';
import { Check, Copy, Download, FileSpreadsheet, Upload, X } from 'lucide-react';
import {
  copyTemplateHeadersToClipboard,
  downloadUniverseTemplate,
  parseSpreadsheet,
  ParsedWorkbookInfo,
} from '../utils/excelParser';

interface ExcelUploadModalProps {
  isOpen: boolean;
  onClose: () => void;
  onProceedToMatch: (parsed: ParsedWorkbookInfo, selectedIdCol: string) => void;
}

export const ExcelUploadModal: React.FC<ExcelUploadModalProps> = ({
  isOpen,
  onClose,
  onProceedToMatch,
}) => {
  const [dragActive, setDragActive] = useState(false);
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [parsedInfo, setParsedInfo] = useState<ParsedWorkbookInfo | null>(null);
  const [selectedSheet, setSelectedSheet] = useState<string>('');
  const [selectedIdCol, setSelectedIdCol] = useState<string>('');
  const [copiedTemplate, setCopiedTemplate] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);

  const fileInputRef = useRef<HTMLInputElement>(null);

  if (!isOpen) return null;

  const handleFileProcess = async (file: File) => {
    setIsLoading(true);
    setErrorMsg(null);
    try {
      setSelectedFile(file);
      const parsed = await parseSpreadsheet(file);
      setParsedInfo(parsed);
      setSelectedSheet(parsed.selectedSheet);
      setSelectedIdCol(parsed.autoDetectedIdCol || (parsed.headers[0] ?? ''));
    } catch (err: any) {
      setErrorMsg(err.message || 'Failed to read spreadsheet file');
    } finally {
      setIsLoading(false);
    }
  };

  const handleSheetChange = async (sheet: string) => {
    if (!selectedFile) return;
    setIsLoading(true);
    try {
      setSelectedSheet(sheet);
      const parsed = await parseSpreadsheet(selectedFile, sheet);
      setParsedInfo(parsed);
      setSelectedIdCol(parsed.autoDetectedIdCol || (parsed.headers[0] ?? ''));
    } catch (err: any) {
      setErrorMsg(err.message || 'Failed to parse sheet');
    } finally {
      setIsLoading(false);
    }
  };

  const handleDrag = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === 'dragenter' || e.type === 'dragover') {
      setDragActive(true);
    } else if (e.type === 'dragleave') {
      setDragActive(false);
    }
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      handleFileProcess(e.dataTransfer.files[0]);
    }
  };

  const handleCopyHeaders = async () => {
    await copyTemplateHeadersToClipboard();
    setCopiedTemplate(true);
    setTimeout(() => setCopiedTemplate(false), 2000);
  };

  const handleProceed = () => {
    if (!parsedInfo || !selectedIdCol) return;
    onProceedToMatch(parsedInfo, selectedIdCol);
  };

  return (
    <div className="center-modal-backdrop" onClick={onClose}>
      <div
        className="center-modal-card"
        style={{ width: 'min(640px, 92vw)' }}
        onClick={(e) => e.stopPropagation()}
      >
        <div className="center-modal-header">
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <FileSpreadsheet size={18} color="var(--link-blue)" />
            <h3 style={{ fontSize: '16px', fontWeight: 600 }}>Upload Stock Universe</h3>
          </div>
          <button className="btn-outline" style={{ border: 'none' }} onClick={onClose}>
            <X size={18} />
          </button>
        </div>

        <div className="center-modal-body" style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
          {/* Template helper banner */}
          <div
            style={{
              padding: '12px 14px',
              backgroundColor: 'var(--panel-secondary)',
              borderRadius: '6px',
              fontSize: '12px',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'space-between',
              gap: '12px',
              border: '1px solid var(--border)',
            }}
          >
            <div>
              <span style={{ fontWeight: 600, color: 'var(--text-primary)' }}>Need a template? </span>
              <span style={{ color: 'var(--text-secondary)' }}>
                Prefill your sheet using canonical column headers.
              </span>
            </div>
            <div style={{ display: 'flex', gap: '8px', flexShrink: 0 }}>
              <button
                type="button"
                className="btn-outline"
                style={{ fontSize: '12px', padding: '5px 10px' }}
                onClick={handleCopyHeaders}
              >
                {copiedTemplate ? <Check size={14} color="#16a34a" /> : <Copy size={14} />}
                {copiedTemplate ? 'Copied' : 'Copy Headers'}
              </button>
              <button
                type="button"
                className="btn-outline"
                style={{ fontSize: '12px', padding: '5px 10px' }}
                onClick={downloadUniverseTemplate}
              >
                <Download size={14} />
                Template .xlsx
              </button>
            </div>
          </div>

          {/* Drag & Drop Zone */}
          <div
            onDragEnter={handleDrag}
            onDragLeave={handleDrag}
            onDragOver={handleDrag}
            onDrop={handleDrop}
            onClick={() => fileInputRef.current?.click()}
            style={{
              border: `2px dashed ${dragActive ? 'var(--link-blue)' : 'var(--border)'}`,
              borderRadius: '8px',
              padding: '38px 20px',
              textAlign: 'center',
              backgroundColor: dragActive ? 'rgba(37, 99, 235, 0.05)' : 'var(--panel-secondary)',
              cursor: 'pointer',
              transition: 'all 0.15s ease',
            }}
          >
            <input
              ref={fileInputRef}
              type="file"
              accept=".xlsx,.xls,.csv"
              style={{ display: 'none' }}
              onChange={(e) => {
                if (e.target.files && e.target.files[0]) {
                  handleFileProcess(e.target.files[0]);
                }
              }}
            />
            <Upload size={30} color="var(--link-blue)" style={{ margin: '0 auto 10px', display: 'block' }} />
            <p style={{ fontWeight: 600, fontSize: '14px', marginBottom: '4px', color: 'var(--text-primary)' }}>
              {selectedFile ? selectedFile.name : 'Click to select or drag & drop spreadsheet'}
            </p>
            <p style={{ fontSize: '12px', color: 'var(--text-secondary)' }}>
              Supports Excel (.xlsx, .xls) and Comma-Separated Values (.csv)
            </p>
          </div>

          {errorMsg && (
            <div style={{ color: '#dc2626', fontSize: '12px', padding: '8px 12px', background: 'rgba(220, 38, 38, 0.08)', borderRadius: '6px' }}>
              {errorMsg}
            </div>
          )}

          {parsedInfo && (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
              {parsedInfo.sheetNames.length > 1 && (
                <div>
                  <label style={{ display: 'block', fontSize: '12px', fontWeight: 600, color: 'var(--text-secondary)', marginBottom: '4px' }}>
                    Select Sheet
                  </label>
                  <select
                    value={selectedSheet}
                    onChange={(e) => handleSheetChange(e.target.value)}
                    style={{
                      width: '100%',
                      padding: '7px 10px',
                      borderRadius: '4px',
                      border: '1px solid var(--border)',
                      background: 'var(--bg)',
                      color: 'var(--text-primary)',
                    }}
                  >
                    {parsedInfo.sheetNames.map((sheet) => (
                      <option key={sheet} value={sheet}>{sheet}</option>
                    ))}
                  </select>
                </div>
              )}

              <div>
                <label style={{ display: 'block', fontSize: '12px', fontWeight: 600, color: 'var(--text-secondary)', marginBottom: '4px' }}>
                  Stock Identifier Column <span style={{ fontWeight: 400, color: 'var(--link-blue)' }}>(Auto-detected: {parsedInfo.autoDetectedIdCol})</span>
                </label>
                <select
                  value={selectedIdCol}
                  onChange={(e) => setSelectedIdCol(e.target.value)}
                  style={{
                    width: '100%',
                    padding: '7px 10px',
                    borderRadius: '4px',
                    border: '1px solid var(--border)',
                    background: 'var(--bg)',
                    color: 'var(--text-primary)',
                  }}
                >
                  {parsedInfo.headers.map((h) => (
                    <option key={h} value={h}>{h}</option>
                  ))}
                </select>
              </div>

              <div style={{ fontSize: '12px', color: 'var(--text-secondary)', display: 'flex', gap: '12px', flexWrap: 'wrap' }}>
                <span>Custom Columns:</span>
                {parsedInfo.detectedCustomCols.quantity && (
                  <span style={{ color: '#16a34a', fontWeight: 600 }}>✓ Quantity ({parsedInfo.detectedCustomCols.quantity})</span>
                )}
                {parsedInfo.detectedCustomCols.buy_price && (
                  <span style={{ color: '#16a34a', fontWeight: 600 }}>✓ Buy Price ({parsedInfo.detectedCustomCols.buy_price})</span>
                )}
                {parsedInfo.detectedCustomCols.notes && (
                  <span style={{ color: '#16a34a', fontWeight: 600 }}>✓ Notes ({parsedInfo.detectedCustomCols.notes})</span>
                )}
                {!parsedInfo.detectedCustomCols.quantity && !parsedInfo.detectedCustomCols.buy_price && (
                  <span>None detected</span>
                )}
              </div>

              <div style={{ fontSize: '13px', color: 'var(--text-primary)' }}>
                <b>{parsedInfo.rows.length} rows</b> ready in sheet "{selectedSheet}".
              </div>
            </div>
          )}
        </div>

        <div className="center-modal-footer">
          <button className="btn-outline" onClick={onClose}>Cancel</button>
          <button
            className="btn-primary"
            disabled={!parsedInfo || parsedInfo.rows.length === 0 || isLoading}
            onClick={handleProceed}
          >
            {isLoading ? 'Processing...' : 'Inspect & Match Universe →'}
          </button>
        </div>
      </div>
    </div>
  );
};
