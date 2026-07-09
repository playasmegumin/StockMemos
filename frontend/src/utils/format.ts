import dayjs from 'dayjs'
import utc from 'dayjs/plugin/utc'
dayjs.extend(utc)

/**
 * Formats a number to Chinese abbreviation (万/亿).
 * >1亿 → "X.XX 亿", >1万 → "X.XX 万", otherwise raw number.
 */
export function fmtAmount(val: number | null | undefined, unit: string = ''): string {
  if (val == null) return '--'
  const abs = Math.abs(val)
  let display: string
  if (abs >= 100_000_000) {
    display = (val / 100_000_000).toFixed(2) + ' 亿'
  } else if (abs >= 10_000) {
    display = (val / 10_000).toFixed(2) + ' 万'
  } else {
    display = val.toFixed(2)
  }
  return unit ? display + ' ' + unit : display
}

/**
 * Formats PnL value with sign and color class.
 */
export function fmtPnl(val: number | null | undefined): { text: string; cls: string } {
  if (val == null) return { text: '--', cls: '' }
  const sign = val >= 0 ? '+' : ''
  const prefix = val > 0 ? '+' : ''
  return {
    text: `${prefix}${fmtAmount(val)}`,
    cls: val >= 0 ? 'text-red-600' : 'text-green-600',
  }
}

/**
 * Formats a percentage (e.g., 15.2 → "15.20%").
 */
export function fmtPercent(val: number | null | undefined): string {
  if (val == null) return '--'
  return val.toFixed(2) + '%'
}

/**
 * Formats a decimal to 2 places.
 */
export function fmtDecimal(val: number | null | undefined): string {
  if (val == null) return '--'
  return val.toFixed(2)
}

/**
 * Formats a stock price (no thousands separator).
 */
export function fmtPrice(val: number | null | undefined, currency?: string): string {
  if (val == null) return '--'
  const s = val.toFixed(2)
  return currency ? `${s} ${currency}` : s
}

/**
 * Formats an ISO datetime string to UTC+8 "YY-MM-DD HH:MM".
 */
export function fmtTime(iso: string | null | undefined, def: string = '--'): string {
  if (!iso) return def
  const d = dayjs.utc(iso).add(8, 'hour')
  return d.format('YY-MM-DD HH:mm')
}

/**
 * Formats a date string to "YYYY-MM-DD".
 */
export function fmtDate(iso: string | null | undefined): string {
  if (!iso) return '--'
  return dayjs.utc(iso).add(8, 'hour').format('YYYY-MM-DD')
}
