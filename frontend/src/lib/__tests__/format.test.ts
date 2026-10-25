import { describe, expect, it } from 'vitest'
import { daysLabel, fmtAmount, fmtDateTime, fmtPct } from '../format'

describe('format helpers', () => {
  it('formats amounts with thousand separators and 2 decimals', () => {
    expect(fmtAmount(490000)).toBe('490,000.00')
    expect(fmtAmount(-45000)).toBe('-45,000.00')
    expect(fmtAmount(0.5)).toBe('0.50')
  })

  it('formats percentages with explicit sign', () => {
    expect(fmtPct(69.2)).toBe('+69.2%')
    expect(fmtPct(-12)).toBe('-12.0%')
    expect(fmtPct(0)).toBe('0.0%')
  })

  it('humanizes deadline distance', () => {
    expect(daysLabel(10)).toBe('10d left')
    expect(daysLabel(0)).toBe('due today')
    expect(daysLabel(-5)).toBe('5d overdue')
  })

  it('falls back to raw input on unparsable dates', () => {
    expect(fmtDateTime('not-a-date')).toBe('not-a-date')
    expect(fmtDateTime('2026-10-13T10:00:00Z')).not.toBe('2026-10-13T10:00:00Z')
  })
})
