import * as XLSX from 'xlsx';

export interface ParsedWorkbookInfo {
  sheetNames: string[];
  selectedSheet: string;
  headers: string[];
  autoDetectedIdCol: string | null;
  detectedCustomCols: {
    quantity: string | null;
    buy_price: string | null;
    notes: string | null;
    date: string | null;
  };
  rows: Record<string, any>[];
}

const ID_PATTERNS = [
  /\bisin\b/i,
  /\b(nse[_\s]?)?symbol\b/i,
  /\bticker\b/i,
  /\bbse[_\s]?code\b/i,
  /\bscrip[_\s]?code\b/i,
  /\bcompany([_\s]?name)?\b/i,
  /\bsecurity([_\s]?name)?\b/i,
  /\bscheme([_\s]?name)?\b/i,
  /\bstock([_\s]?name)?\b/i,
  /\bname\b/i,
];

const CUSTOM_PATTERNS = {
  quantity: ['quantity', 'qty', 'shares', 'units', 'holding_qty'],
  buy_price: ['buy_price', 'purchase_price', 'cost_price', 'avg_price', 'avg_cost', 'entry_price', 'cost'],
  notes: ['notes', 'remarks', 'comment', 'tags'],
  date: ['buy_date', 'purchase_date', 'trade_date', 'date'],
};

export function inspectWorkbookSheets(file: File): Promise<string[]> {
  return new Promise((resolve, reject) => {
    const reader = new FileReader();
    reader.onload = (e) => {
      try {
        const data = new Uint8Array(e.target?.result as ArrayBuffer);
        const workbook = XLSX.read(data, { type: 'array' });
        resolve(workbook.SheetNames);
      } catch (err) {
        reject(err);
      }
    };
    reader.onerror = reject;
    reader.readAsArrayBuffer(file);
  });
}

export function parseSpreadsheet(file: File, sheetName?: string): Promise<ParsedWorkbookInfo> {
  return new Promise((resolve, reject) => {
    const reader = new FileReader();
    reader.onload = (e) => {
      try {
        const data = new Uint8Array(e.target?.result as ArrayBuffer);
        const workbook = XLSX.read(data, { type: 'array' });
        const sheetNames = workbook.SheetNames;
        const targetSheet = sheetName && sheetNames.includes(sheetName) ? sheetName : sheetNames[0];
        const worksheet = workbook.Sheets[targetSheet];

        const rawJson: any[] = XLSX.utils.sheet_to_json(worksheet, { defval: '' });
        if (rawJson.length === 0) {
          resolve({
            sheetNames,
            selectedSheet: targetSheet,
            headers: [],
            autoDetectedIdCol: null,
            detectedCustomCols: { quantity: null, buy_price: null, notes: null, date: null },
            rows: [],
          });
          return;
        }

        const headers = Object.keys(rawJson[0]);

        // Auto-detect identifier column
        let autoDetectedIdCol: string | null = null;
        for (const pattern of ID_PATTERNS) {
          const match = headers.find((h) => pattern.test(h.trim()));
          if (match) {
            autoDetectedIdCol = match;
            break;
          }
        }
        if (!autoDetectedIdCol && headers.length > 0) {
          autoDetectedIdCol = headers[0];
        }

        // Detect custom columns
        const detectedCustomCols: {
          quantity: string | null;
          buy_price: string | null;
          notes: string | null;
          date: string | null;
        } = {
          quantity: null,
          buy_price: null,
          notes: null,
          date: null,
        };

        for (const [key, keywords] of Object.entries(CUSTOM_PATTERNS)) {
          const found = headers.find((h) => {
            const clean = h.trim().toLowerCase();
            return keywords.some((kw) => clean === kw || clean.includes(kw));
          });
          detectedCustomCols[key as keyof typeof detectedCustomCols] = found || null;
        }

        resolve({
          sheetNames,
          selectedSheet: targetSheet,
          headers,
          autoDetectedIdCol,
          detectedCustomCols,
          rows: rawJson,
        });
      } catch (err) {
        reject(err);
      }
    };
    reader.onerror = reject;
    reader.readAsArrayBuffer(file);
  });
}

export function downloadUniverseTemplate() {
  const headers = [
    'Company Name',
    'NSE Symbol',
    'ISIN',
    'BSE Code',
    'Quantity',
    'Buy Price',
    'Notes',
  ];
  const sampleRow = [
    'Reliance Industries Limited',
    'RELIANCE',
    'INE002A01018',
    '500325',
    '50',
    '2420.50',
    'Core Holding',
  ];

  const ws = XLSX.utils.aoa_to_sheet([headers, sampleRow]);
  const wb = XLSX.utils.book_new();
  XLSX.utils.book_append_sheet(wb, ws, 'Template');
  XLSX.writeFile(wb, 'stock_screener_universe_template.xlsx');
}

export function copyTemplateHeadersToClipboard(): Promise<void> {
  const headers = [
    'Company Name',
    'NSE Symbol',
    'ISIN',
    'BSE Code',
    'Quantity',
    'Buy Price',
    'Notes',
  ];
  return navigator.clipboard.writeText(headers.join(','));
}
