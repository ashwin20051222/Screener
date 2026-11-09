export const formatIndianNumber = (
  val: number | null | undefined,
  decimals: number = 2
): string => {
  if (val === null || val === undefined || isNaN(val)) return '–';
  return val.toLocaleString('en-IN', {
    minimumFractionDigits: decimals,
    maximumFractionDigits: decimals,
  });
};

export const round2 = (v: number | null | undefined): string => {
  if (v === null || v === undefined || isNaN(v)) return '';
  return String(Math.round(v * 100) / 100);
};

export const isPercentageMetric = (name: string): boolean => {
  return /return|growth|margin|yield|holding|premium|payout|roce|upside|reco|rollover|change in|vs nifty|cagr|expense ratio|tracking|volatility|max loss|away from|above|alpha|% /i.test(
    name
  );
};
