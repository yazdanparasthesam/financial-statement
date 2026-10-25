import { describe, expect, it } from 'vitest'
import { groupBySeverity, severityBadge, summarize } from '../validation'
import type { ValidationResult } from '../../api/types'

const R = (rule_id: string, severity: ValidationResult['severity'], passed: boolean): ValidationResult =>
  ({ rule_id, severity, passed, message: `${rule_id} ${passed ? 'ok' : 'failed'}` })

describe('validation summary', () => {
  const results = [R('R001', 'error', true), R('R002', 'error', false), R('R003', 'warning', false),
    R('R004', 'error', true), R('R005', 'warning', true), R('R006', 'info', true)]

  it('counts totals and failures', () => {
    const s = summarize(results)
    expect(s.total).toBe(6)
    expect(s.passed).toBe(4)
    expect(s.failed).toBe(2)
  })

  it('failing error blocks submission', () => {
    expect(summarize(results).canSubmit).toBe(false)
    expect(summarize(results).failedErrors.map((r) => r.rule_id)).toEqual(['R002'])
  })

  it('warnings alone do NOT block submission (matches backend gate)', () => {
    const warnOnly = [R('R001', 'error', true), R('R003', 'warning', false), R('R006', 'warning', false)]
    const s = summarize(warnOnly)
    expect(s.canSubmit).toBe(true)
    expect(s.failedWarnings).toHaveLength(2)
  })

  it('groups by severity', () => {
    const g = groupBySeverity(results)
    expect(g.error).toHaveLength(3)
    expect(g.warning).toHaveLength(2)
    expect(g.info).toHaveLength(1)
  })

  it('badge colors per severity', () => {
    expect(severityBadge('error')).toContain('red')
    expect(severityBadge('warning')).toContain('amber')
    expect(severityBadge('info')).toContain('slate')
  })
})
