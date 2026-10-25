/** Validation-report logic (pure — covered by vitest). Mirrors backend severities:
 *  failing 'error' rules block submission; warnings/info do not. */
import type { Severity, ValidationResult } from '../api/types'

export interface ValidationSummary {
  total: number
  passed: number
  failed: number
  failedErrors: ValidationResult[]
  failedWarnings: ValidationResult[]
  canSubmit: boolean
}

export function summarize(results: ValidationResult[]): ValidationSummary {
  const failed = results.filter((r) => !r.passed)
  const failedErrors = failed.filter((r) => r.severity === 'error')
  const failedWarnings = failed.filter((r) => r.severity === 'warning')
  return {
    total: results.length,
    passed: results.length - failed.length,
    failed: failed.length,
    failedErrors,
    failedWarnings,
    canSubmit: failedErrors.length === 0,
  }
}

export function groupBySeverity(results: ValidationResult[]): Record<Severity, ValidationResult[]> {
  const groups: Record<Severity, ValidationResult[]> = { error: [], warning: [], info: [] }
  for (const r of results) groups[r.severity]?.push(r)
  return groups
}

export function severityBadge(sev: Severity): string {
  return sev === 'error' ? 'bg-red-100 text-red-800'
    : sev === 'warning' ? 'bg-amber-100 text-amber-800'
    : 'bg-slate-100 text-slate-600'
}
