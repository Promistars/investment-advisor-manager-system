import type { UserPrefs } from './api'
import type { Lang } from './i18n'

const VIEW_PREF_TO_API: Record<string, string> = {
  month: 'monthly',
  quarter: 'quarterly',
  year: 'yearly',
  monthly: 'monthly',
  quarterly: 'quarterly',
  yearly: 'yearly',
  custom: 'custom',
}

const VIEW_API_TO_PREF: Record<string, UserPrefs['default_view']> = {
  monthly: 'month',
  quarterly: 'quarter',
  yearly: 'year',
  custom: 'month',
}

export function normalizeLang(raw: unknown): Lang {
  const s = String(raw ?? '')
    .trim()
    .toLowerCase()
  if (s === 'zh' || s === 'chinese' || s === 'cn' || s === '中文') return 'zh'
  if (s === 'en' || s === 'english' || s === '英文') return 'en'
  return 'zh'
}

export function normalizePnlColors(raw: unknown, lang: Lang): UserPrefs['pnl_colors'] {
  const s = String(raw ?? '').toLowerCase()
  if (s === 'cn' || s.includes('red up') || s.includes('a股') || s.includes('chinese')) return 'cn'
  if (s === 'western' || s.includes('green up') || s.includes('western')) return 'western'
  return lang === 'zh' ? 'cn' : 'western'
}

export function normalizeDateFormat(raw: unknown): UserPrefs['date_format'] {
  const s = String(raw ?? 'iso')
  if (s === 'cn' || s === 'us' || s === 'iso') return s
  return 'iso'
}

export function normalizeDefaultView(raw: unknown): UserPrefs['default_view'] {
  const s = String(raw ?? 'month').toLowerCase()
  if (s === 'month' || s === 'monthly') return 'month'
  if (s === 'quarter' || s === 'quarterly') return 'quarter'
  if (s === 'year' || s === 'yearly') return 'year'
  return 'month'
}

export function prefViewToApi(view: string): string {
  return VIEW_PREF_TO_API[view] ?? view
}

export function apiViewToPref(view: string): UserPrefs['default_view'] {
  return VIEW_API_TO_PREF[view] ?? 'month'
}

export function normalizePrefs(raw: Partial<UserPrefs> & Record<string, unknown>): UserPrefs {
  const lang = normalizeLang(raw.lang)
  return {
    lang,
    pnl_colors: normalizePnlColors(raw.pnl_colors, lang),
    date_format: normalizeDateFormat(raw.date_format),
    compact_ui: Boolean(raw.compact_ui),
    show_emoji: raw.show_emoji !== false,
    default_view: normalizeDefaultView(raw.default_view),
  }
}

export function pnlColorsForLang(lang: Lang): UserPrefs['pnl_colors'] {
  return lang === 'zh' ? 'cn' : 'western'
}
