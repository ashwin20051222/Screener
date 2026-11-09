import * as XLSX from 'xlsx';
import { StockRow, FilterDefinition } from '../types';

export function exportTableData(
  rows: StockRow[],
  columnIds: string[],
  filterMap: Map<string, FilterDefinition>,
  format: 'csv' | 'xlsx'
) {
  // Construct headers: Index, Name, Sub-Sector, then metric labels
  const headers = [
    '#',
    'Name',
    'Sub-Sector',
    'Sector',
    ...columnIds.map(id => {
      const f = filterMap.get(id);
      return f ? `${f.name}${f.unit ? ` (${f.unit})` : ''}` : id;
    }),
  ];

  // Construct rows
  const data = rows.map((r, i) => [
    i + 1,
    r.name,
    r.sub,
    r.sector,
    ...columnIds.map(id => r.v[id] ?? ''),
  ]);

  const worksheet = XLSX.utils.aoa_to_sheet([headers, ...data]);
  const workbook = XLSX.utils.book_new();
  XLSX.utils.book_append_sheet(workbook, worksheet, 'Stock Screener');

  const timestamp = new Date().toISOString().split('T')[0];
  const filename = `stock_screener_${timestamp}.${format}`;

  if (format === 'csv') {
    XLSX.writeFile(workbook, filename, { bookType: 'csv' });
  } else {
    XLSX.writeFile(workbook, filename, { bookType: 'xlsx' });
  }
}
