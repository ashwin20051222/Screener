import { StockRow, FilterDefinition } from '../types';

export const slugify = (s: string): string =>
  String(s)
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, '_')
    .replace(/^_+|_+$/g, '');

export function compileCustomFilter(
  src: string,
  filterMap: Map<string, FilterDefinition>
): { fn: (r: StockRow) => number | null; metricIds: string[] } {
  const clean = src.trim();
  if (!clean) throw new Error('Formula cannot be empty');

  const tokens = clean.match(/\[[^\]]+\]|\d+\.?\d*|[()+\-*/]/g) || [];
  if (tokens.join('').replace(/\s/g, '') !== clean.replace(/\s/g, '')) {
    throw new Error('Unexpected characters in formula');
  }

  let p = 0;
  const usedIds = new Set<string>();

  const expr = (): ((r: StockRow) => number | null) => {
    let a = term();
    while (tokens[p] === '+' || tokens[p] === '-') {
      const op = tokens[p++];
      const b = term();
      const prevA = a;
      a = (r: StockRow) => {
        const l = prevA(r);
        const q = b(r);
        if (l === null || q === null) return null;
        return op === '+' ? l + q : l - q;
      };
    }
    return a;
  };

  const term = (): ((r: StockRow) => number | null) => {
    let a = factor();
    while (tokens[p] === '*' || tokens[p] === '/') {
      const op = tokens[p++];
      const b = factor();
      const prevA = a;
      a = (r: StockRow) => {
        const l = prevA(r);
        const q = b(r);
        if (l === null || q === null || (op === '/' && q === 0)) return null;
        return op === '*' ? l * q : l / q;
      };
    }
    return a;
  };

  const factor = (): ((r: StockRow) => number | null) => {
    const t = tokens[p++];
    if (t === '(') {
      const a = expr();
      if (tokens[p++] !== ')') throw new Error('Missing closing parenthesis )');
      return a;
    }
    if (t && t.startsWith('[') && t.endsWith(']')) {
      const rawName = t.slice(1, -1);
      const id = slugify(rawName);
      if (!filterMap.has(id)) {
        // Also check if matches any filter by label directly
        const matched = Array.from(filterMap.values()).find(
          f => f.name.toLowerCase() === rawName.toLowerCase()
        );
        if (matched) {
          usedIds.add(matched.id);
          return (r: StockRow) => r.v[matched.id] ?? null;
        }
        throw new Error(`Unknown metric: ${t}`);
      }
      usedIds.add(id);
      return (r: StockRow) => r.v[id] ?? null;
    }
    if (t && /^\d/.test(t)) {
      const num = parseFloat(t);
      return () => num;
    }
    if (t === '-') {
      const a = factor();
      return (r: StockRow) => {
        const v = a(r);
        return v === null ? null : -v;
      };
    }
    throw new Error(`Syntax error near "${t || 'end of formula'}"`);
  };

  const compiledFn = expr();
  if (p < tokens.length) throw new Error('Syntax error: extra input after formula');
  if (usedIds.size < 2 || usedIds.size > 5) {
    throw new Error('Custom filter must combine between 2 and 5 data items');
  }

  return { fn: compiledFn, metricIds: Array.from(usedIds) };
}
