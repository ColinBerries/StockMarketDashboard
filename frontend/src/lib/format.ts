export const formatCurrency = (value: number | null | undefined): string => {
  if (value === null || value === undefined || Number.isNaN(value)) return "—";
  return `$${value.toFixed(2)}`;
};

export const formatPercent = (value: number | null | undefined, digits = 2): string => {
  if (value === null || value === undefined || Number.isNaN(value)) return "—";
  const sign = value > 0 ? "+" : "";
  return `${sign}${value.toFixed(digits)}%`;
};

export const formatCompact = (value: number | null | undefined): string => {
  if (value === null || value === undefined || Number.isNaN(value)) return "—";
  const abs = Math.abs(value);
  if (abs >= 1_000_000_000) return `${(value / 1_000_000_000).toFixed(1)}B`;
  if (abs >= 1_000_000) return `${(value / 1_000_000).toFixed(1)}M`;
  if (abs >= 1_000) return `${(value / 1_000).toFixed(1)}K`;
  return value.toFixed(0);
};

export const formatNumber = (value: number | null | undefined, digits = 2): string => {
  if (value === null || value === undefined || Number.isNaN(value)) return "—";
  return value.toFixed(digits);
};

/**
 * Right-aligns a series that's shorter than the date axis (e.g. an EMA
 * series that drops its warm-up period) by left-padding with nulls, so it
 * can be zipped index-for-index against a full-length dates array.
 */
export function alignRight<T>(
  length: number,
  series: (T | null)[] | null | undefined,
): (T | null)[] {
  if (!series) return Array(length).fill(null);
  const offset = length - series.length;
  if (offset <= 0) return series.slice(series.length - length);
  return [...Array(offset).fill(null), ...series];
}
