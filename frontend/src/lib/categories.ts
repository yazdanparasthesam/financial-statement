/** Statutory categories — mirrors backend app/domain/mapping.py ALL_CATEGORIES. */
export const ALL_CATEGORIES = [
  'current_assets', 'non_current_assets', 'current_liabilities', 'non_current_liabilities', 'equity',
  'revenue', 'cogs', 'operating_expenses', 'other_income', 'other_expenses', 'tax_expense',
] as const

export function categoryLabel(c: string): string {
  return c ? c.replace(/_/g, ' ').replace(/\b\w/g, (m) => m.toUpperCase()) : '—'
}
