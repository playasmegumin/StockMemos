import { describe, it, expect } from 'vitest'
import { fmtAmount, fmtPnl, fmtPercent, fmtPrice } from '@/utils/format'

describe('fmtAmount', () => {
  it('returns -- for null/undefined', () => {
    expect(fmtAmount(null)).toBe('--')
    expect(fmtAmount(undefined)).toBe('--')
  })

  it('formats amounts < 1万 as raw number', () => {
    expect(fmtAmount(1234.56)).toBe('1234.56')
    expect(fmtAmount(0)).toBe('0.00')
    expect(fmtAmount(-500)).toBe('-500.00')
  })

  it('formats amounts >= 1万 as 万', () => {
    expect(fmtAmount(12345)).toBe('1.23 万')
    expect(fmtAmount(9999999)).toBe('1000.00 万')
  })

  it('formats amounts >= 1亿 as 亿', () => {
    expect(fmtAmount(100_000_000)).toBe('1.00 亿')
    expect(fmtAmount(1_234_567_890)).toBe('12.35 亿')
  })

  it('appends unit suffix', () => {
    expect(fmtAmount(12345, '¥')).toBe('1.23 万 ¥')
  })
})

describe('fmtPnl', () => {
  it('returns color-coded text', () => {
    const pos = fmtPnl(10000)
    expect(pos.text).toContain('+')
    expect(pos.cls).toContain('red')

    const neg = fmtPnl(-10000)
    expect(neg.text).toContain('-')
    expect(neg.cls).toContain('green')
  })
})

describe('fmtPercent', () => {
  it('formats percentage', () => {
    expect(fmtPercent(15.2)).toBe('15.20%')
    expect(fmtPercent(0)).toBe('0.00%')
  })
})

describe('fmtPrice', () => {
  it('formats with currency', () => {
    expect(fmtPrice(1486.50, '¥')).toBe('1486.50 ¥')
  })
})
