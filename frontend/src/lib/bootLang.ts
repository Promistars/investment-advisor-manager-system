import type { Lang } from './i18n'

/** Language for pre-React boot screens (no AuthContext yet). */
export function bootLang(): Lang {
  if (typeof navigator === 'undefined') return 'zh'
  const n = navigator.language.toLowerCase()
  return n.startsWith('zh') ? 'zh' : 'en'
}
