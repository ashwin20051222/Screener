import React from 'react';
import { Download, Copy } from 'lucide-react';

interface ExportMenuProps {
  isOpen: boolean;
  onClose: () => void;
  onExportCsv: () => void;
  onExportXlsx: () => void;
  onCopyCsv: () => void;
}

export const ExportMenu: React.FC<ExportMenuProps> = ({
  isOpen,
  onClose,
  onExportCsv,
  onExportXlsx,
  onCopyCsv,
}) => {
  if (!isOpen) return null;

  return (
    <div
      style={{
        position: 'absolute',
        right: 40,
        top: 80,
        background: 'var(--bg)',
        border: '1px solid var(--border)',
        borderRadius: '6px',
        boxShadow: 'var(--shadow-modal)',
        padding: '6px 0',
        zIndex: 30,
        minWidth: '180px',
      }}
      onClick={e => e.stopPropagation()}
    >
      <div
        style={{
          padding: '8px 14px',
          cursor: 'pointer',
          display: 'flex',
          alignItems: 'center',
          gap: '8px',
          fontSize: '13px',
          color: 'var(--text-primary)',
        }}
        onClick={() => {
          onExportCsv();
          onClose();
        }}
        onMouseEnter={e => (e.currentTarget.style.background = 'var(--hover-bg)')}
        onMouseLeave={e => (e.currentTarget.style.background = 'transparent')}
      >
        <Download size={14} /> Download CSV (.csv)
      </div>
      <div
        style={{
          padding: '8px 14px',
          cursor: 'pointer',
          display: 'flex',
          alignItems: 'center',
          gap: '8px',
          fontSize: '13px',
          color: 'var(--text-primary)',
        }}
        onClick={() => {
          onExportXlsx();
          onClose();
        }}
        onMouseEnter={e => (e.currentTarget.style.background = 'var(--hover-bg)')}
        onMouseLeave={e => (e.currentTarget.style.background = 'transparent')}
      >
        <Download size={14} /> Download Excel (.xlsx)
      </div>
      <div
        style={{
          padding: '8px 14px',
          cursor: 'pointer',
          display: 'flex',
          alignItems: 'center',
          gap: '8px',
          fontSize: '13px',
          color: 'var(--text-primary)',
          borderTop: '1px solid var(--border-light)',
        }}
        onClick={() => {
          onCopyCsv();
          onClose();
        }}
        onMouseEnter={e => (e.currentTarget.style.background = 'var(--hover-bg)')}
        onMouseLeave={e => (e.currentTarget.style.background = 'transparent')}
      >
        <Copy size={14} /> Copy to Clipboard
      </div>
    </div>
  );
};
