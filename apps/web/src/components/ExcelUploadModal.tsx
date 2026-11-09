import React, { useRef, useState } from 'react';
import { Check, Copy, Download, FileSpreadsheet, Upload, X } from 'lucide-react';
import {
  copyTemplateHeadersToClipboard,
  downloadUniverseTemplate,
  inspectWorkbookSheets,
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
      const file = e.dataTransfer.files[0];
      handleFileProcess(file);
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
    <div className="modal-overlay" onClick={onClose}>
      <div
        className="modal-container"
        style={{ width: '640px', maxHeight: '90vh' }}
        onClick={(e) => e.stopPropagation()}
      >
        {/* Header */}
        <div className="modal-header">
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <FileSpreadsheet size={20} color="var(--primary)" />
            <h2 className="modal-title">Upload Stock Universe</h2>
          </div>
          <button className="modal-close-btn" onClick={onClose}>
            <X size={18} />
          </button>
        </div>

        {/* Body */}
        <div className="modal-body" style={{ padding: '20px 24px', display: 'flex', flexDirection: 'column', gap: '18px' }}>
          {/* Template helper info banner */}
          <div
            style={{
              padding: '12px 16px',
              backgroundColor: 'var(--bg-active)',
              borderRadius: '8px',
              fontSize: '13px',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'space-between',
              border: '1px solid var(--border-color)',
            }}
          >
            <div>
              <span style={{ fontWeight: 600 }}>Need a template? </span>
              <span style={{ color: 'var(--text-muted)' }}>Use our pre-configured column headers.</span>
            </div>
            <div style={{ display: 'flex', gap: '8px' }}>
              <button
                type="button"
                onClick={handleCopyHeaders}
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  gap: '6px',
                  padding: '5px 10px',
                  fontSize: '12px',
                  background: 'var(--bg-card)',
                  border: '1px solid var(--border-color)',
                  borderRadius: '6px',
                  cursor: 'pointer',
                  color: 'var(--text-main)',
                }}
              >
                {copiedTemplate ? <Check size={14} color="#16a34a" /> : <Copy size={14} />}
                {copiedTemplate ? 'Copied' : 'Copy Headers'}
              </button>
              <button
                type="button"
                onClick={downloadUniverseTemplate}
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  gap: '6px',
                  padding: '5px 10px',
                  fontSize: '12px',
                  background: 'var(--bg-card)',
                  border: '1px solid var(--border-color)',
                  borderRadius: '6px',
                  cursor: 'pointer',
                  color: 'var(--text-main)',
                }}
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
              border: `2px dashed ${dragActive ? 'var(--primary)' : 'var(--border-color)'}`,
              borderRadius: '12px',
              padding: '36px 20px',
              textAlign: 'center',
              backgroundColor: dragActive ? 'rgba(0, 102, 255, 0.05)' : 'var(--bg-active)',
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
            <Upload size={32} color="var(--primary)" style={{ margin: '0 auto 10px' }} />
            <p style={{ fontWeight: 600, fontSize: '14px', marginBottom: '4px' }}>
              {selectedFile ? selectedFile.name : 'Click to select or drag & drop spreadsheet'}
            </p>
            <p style={{ fontSize: '12px', color: 'var(--text-muted)' }}>
              Supports Excel (.xlsx, .xls) and Comma-Separated Values (.csv)
            </p>
          </div>

          {errorMsg && (
            <div style={{ color: '#dc2626', fontSize: '13px', padding: '8px 12px', background: 'rgba(220, 38, 38, 0.08)', borderRadius: '6px' }}>
              {errorMsg}
            </div>
          )}

          {/* Configuration when file parsed */}
          {parsedInfo && (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '14px' }}>
              {/* Sheet Selector (if workbook has multiple sheets) */}
              {parsedInfo.sheetNames.length > 1 && (
                <div>
                  <label style={{ display: 'block', fontSize: '12px', fontWeight: 600, color: 'var(--text-muted)', marginBottom: '6px' }}>
                    Select Sheet:
                  </label>
                  <select
                    value={selectedSheet}
                    onChange={(e) => handleSheetChange(e.target.value)}
                    style={{
                      width: '100%',
                      padding: '8px 12px',
                      borderRadius: '6px',
                      border: '1px solid var(--border-color)',
                      background: 'var(--bg-card)',
                      color: 'var(--text-main)',
                      fontSize: '13px',
                    }}
                  >
                    {parsedInfo.sheetNames.map((sheet) => (
                      <option key={sheet} value={sheet}>
                        {sheet}
                      </option>
                    ))}
                  </select>
                </div>
              )}

              {/* Identifier Column Selection */}
              <div>
                <label style={{ display: 'block', fontSize: '12px', fontWeight: 600, color: 'var(--text-muted)', marginBottom: '6px' }}>
                  Stock Identifier Column: <span style={{ fontWeight: 400, color: 'var(--primary)' }}>(Auto-detected: {parsedInfo.autoDetectedIdCol})</span>
                </label>
                <select
                  value={selectedIdCol}
                  onChange={(e) => setSelectedIdCol(e.target.value)}
                  style={{
                    width: '100%',
                    padding: '8px 12px',
                    borderRadius: '6px',
                    border: '1px solid var(--border-color)',
                    background: 'var(--bg-card)',
                    color: 'var(--text-main)',
                    fontSize: '13px',
                  }}
                >
                  {parsedInfo.headers.map((h) => (
                    <option key={h} value={h}>
                      {h}
                    </option>
                  ))}
                </select>
              </div>

              {/* Detected Custom Columns */}
              <div style={{ fontSize: '12px', color: 'var(--text-muted)', display: 'flex', gap: '12px', flexWrap: 'wrap' }}>
                <span>Detected Custom Columns:</span>
                {parsedInfo.detectedCustomCols.quantity && (
                  <span style={{ color: '#16a34a', fontWeight: 600 }}>✓ Quantity ({parsedInfo.detectedCustomCols.quantity})</span>
                )}
                {parsedInfo.detectedCustomCols.buy_price && (
                  <span style={{ color: '#16a34a', fontWeight: 600 }}>✓ Buy Price ({parsedInfo.detectedCustomCols.buy_price})</span>
                )}
                {parsedInfo.detectedCustomCols.notes && (
                  <span style={{ color: '#16a34a', fontWeight: 600 }}>✓ Notes ({parsedInfo.detectedCustomCols.notes})</span>
                )}
              </div>

              <div style={{ fontSize: '13px', color: 'var(--text-main)' }}>
                <strong>{parsedInfo.rows.length} rows</strong> found in sheet "{selectedSheet}".
              </div>
            </div>
          )}
        </div>

        {/* Footer */}
        <div className="modal-footer" style={{ display: 'flex', justifyContent: 'flex-end', gap: '12px' }}>
          <button className="btn-cancel" onClick={onClose}>
            Cancel
          </button>
          <button
            className="btn-apply"
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
