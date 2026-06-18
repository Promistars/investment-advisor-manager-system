import type { UserPrefs } from './api'
import type { Lang } from './i18n'

import { pnlColorsForLang as _pnlColorsForLang } from './prefsNormalize'

export { normalizeLang, normalizePrefs, prefViewToApi, apiViewToPref, pnlColorsForLang } from './prefsNormalize'

const pnlColorsForLang = _pnlColorsForLang

export function round2(n: number): number {
  return Math.round(n * 100) / 100
}

function localeForLang(lang: Lang): string {
  return lang === 'zh' ? 'zh-CN' : 'en-US'
}

export function fmtNum(n: number | null | undefined, lang: Lang = 'zh', digits = 2): string {
  if (n == null || !Number.isFinite(n)) return '—'
  return n.toLocaleString(localeForLang(lang), { minimumFractionDigits: digits, maximumFractionDigits: digits })
}

/** 表格单元格：数字统一两位小数，其余原样 */
export function fmtCell(v: unknown, lang: Lang = 'zh'): string {
  if (v == null || v === '') return ''
  if (typeof v === 'number' && Number.isFinite(v)) return fmtNum(v, lang)
  if (typeof v === 'string') {
    const t = v.trim()
    if (t && /^-?\d+(\.\d+)?([eE][+-]?\d+)?$/.test(t)) return fmtNum(Number(t), lang)
  }
  return String(v)
}

export function fmtMoney(n: number, prefs: UserPrefs | Lang = 'zh', compact = false) {
  const lang: Lang = typeof prefs === 'string' ? prefs : prefs.lang
  if (!Number.isFinite(n)) return '—'
  if (compact && Math.abs(n) >= 10000) {
    const wan = lang === 'zh' ? '万' : 'w'
    return `¥${(n / 10000).toFixed(2)}${wan}`
  }
  return `¥${n.toLocaleString(localeForLang(lang), { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`
}

export function fmtPct(n: number, signed = true) {
  if (!Number.isFinite(n)) return '—'
  const prefix = signed && n > 0 ? '+' : ''
  return `${prefix}${n.toFixed(2)}%`
}

export function pnlClass(value: number, prefs: UserPrefs) {
  const cn = pnlColorsForLang(prefs.lang) === 'cn'
  const up = cn ? 'pnl-up-cn' : 'pnl-up-west'
  const down = cn ? 'pnl-down-cn' : 'pnl-down-west'
  if (value > 0) return up
  if (value < 0) return down
  return 'text-stone-500'
}

export function fmtDate(iso: string, prefs: UserPrefs) {
  if (!iso) return '—'
  const d = iso.slice(0, 10)
  if (prefs.date_format === 'cn') {
    const [y, m, day] = d.split('-')
    return `${y}年${m}月${day}日`
  }
  if (prefs.date_format === 'us') {
    const [y, m, day] = d.split('-')
    return `${m}/${day}/${y}`
  }
  return d
}
