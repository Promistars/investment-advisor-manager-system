import { useMutation } from '@tanstack/react-query'
import { useEffect, useState } from 'react'
import { useAuth } from '../context/AuthContext'
import { api } from '../lib/api'
import { pnlColorsForLang } from '../lib/format'
import { t, e } from '../lib/i18n'

export function SettingsPage() {
  const { prefs, setPrefs, refreshPrefs, user } = useAuth()
  const lang = prefs.lang
  const [local, setLocal] = useState(prefs)
  const [saved, setSaved] = useState(false)
  const [oldPwd, setOldPwd] = useState('')
  const [newPwd, setNewPwd] = useState('')
  const [pwdMsg, setPwdMsg] = useState('')
  const [maintMsg, setMaintMsg] = useState('')

  useEffect(() => {
    setLocal(prefs)
  }, [prefs])

  const saveMut = useMutation({
    mutationFn: () => api.savePrefs({ ...local, pnl_colors: pnlColorsForLang(local.lang) }),
    onSuccess: async () => {
      setPrefs(local)
      await refreshPrefs()
      setSaved(true)
      setTimeout(() => setSaved(false), 2000)
    },
  })

  const resetMut = useMutation({
    mutationFn: () => api.resetPrefs(),
    onSuccess: async (p) => {
      setLocal(p)
      setPrefs(p)
      await refreshPrefs()
      setMaintMsg(t('settings.reset_ok', lang))
      setTimeout(() => setMaintMsg(''), 3000)
    },
  })

  const refreshMut = useMutation({
    mutationFn: () => api.refreshPnl(),
    onSuccess: () => {
      setMaintMsg(t('settings.refresh_pnl_ok', lang))
      setTimeout(() => setMaintMsg(''), 3000)
    },
  })

  const pwdMut = useMutation({
    mutationFn: () => api.changePassword(oldPwd, newPwd),
    onSuccess: () => {
      setPwdMsg(t('auth.change_ok', lang))
      setOldPwd('')
      setNewPwd('')
    },
    onError: (e) => setPwdMsg(e instanceof Error ? e.message : t('common.error', lang)),
  })

  const confirmRefresh = () => {
    if (window.confirm(t('settings.confirm_refresh_msg', lang))) refreshMut.mutate()
  }

  const confirmReset = () => {
    if (window.confirm(t('settings.confirm_reset_msg', lang))) resetMut.mutate()
  }

  return (
    <div className="max-w-xl space-y-6">
      <h2 className="text-2xl font-bold text-stone-800">{e('settings.title', lang, '⚙️', prefs.show_emoji)}</h2>

      <div className="card p-6 space-y-4">
        <div>
          <label className="text-sm text-stone-600">{t('settings.lang', lang)}</label>
          <select
            className="input mt-1"
            value={local.lang}
            onChange={(e) => {
              const nextLang = e.target.value as 'zh' | 'en'
              setLocal({ ...local, lang: nextLang, pnl_colors: pnlColorsForLang(nextLang) })
            }}
          >
            <option value="zh">{t('settings.lang.zh', lang)}</option>
            <option value="en">{t('settings.lang.en', lang)}</option>
          </select>
        </div>
        <div>
          <label className="text-sm text-stone-600">{t('settings.date_format', lang)}</label>
          <select className="input mt-1" value={local.date_format} onChange={(e) => setLocal({ ...local, date_format: e.target.value as 'iso' | 'cn' | 'us' })}>
            <option value="iso">{t('settings.date_iso', lang)}</option>
            <option value="cn">{t('settings.date_cn', lang)}</option>
            <option value="us">{t('settings.date_us', lang)}</option>
          </select>
        </div>
        <div>
          <label className="text-sm text-stone-600">{t('settings.default_view', lang)}</label>
          <select className="input mt-1" value={local.default_view} onChange={(e) => setLocal({ ...local, default_view: e.target.value as 'month' | 'quarter' | 'year' })}>
            <option value="month">{t('settings.view_month', lang)}</option>
            <option value="quarter">{t('settings.view_quarter', lang)}</option>
            <option value="year">{t('settings.view_year', lang)}</option>
          </select>
        </div>
        <label className="flex items-center gap-2 text-sm">
          <input type="checkbox" checked={local.show_emoji} onChange={(e) => setLocal({ ...local, show_emoji: e.target.checked })} />
          {t('settings.emoji', lang)}
        </label>
        <label className="flex items-center gap-2 text-sm">
          <input type="checkbox" checked={local.compact_ui} onChange={(e) => setLocal({ ...local, compact_ui: e.target.checked })} />
          {t('settings.compact', lang)}
        </label>
        <button type="button" className="btn-primary" onClick={() => saveMut.mutate()} disabled={saveMut.isPending}>
          {t('settings.save', lang)}
        </button>
        {saved && <span className="text-sm text-green-600 ml-2">{t('settings.saved', lang)}</span>}
      </div>

      {user && (
        <div className="card p-6 space-y-3">
          <h3 className="font-semibold">{t('auth.change_pwd', lang)}</h3>
          <input type="password" className="input" placeholder={t('auth.old_pwd', lang)} value={oldPwd} onChange={(e) => setOldPwd(e.target.value)} />
          <input type="password" className="input" placeholder={t('auth.new_pwd', lang)} value={newPwd} onChange={(e) => setNewPwd(e.target.value)} />
          <button type="button" className="btn-secondary" onClick={() => pwdMut.mutate()} disabled={!oldPwd || !newPwd}>
            {t('auth.change_pwd', lang)}
          </button>
          {pwdMsg && <p className="text-sm text-stone-600">{pwdMsg}</p>}
        </div>
      )}

      <div className="card p-6 space-y-3 border-dashed">
        <h3 className="text-sm font-semibold text-stone-500">{t('settings.advanced_fold', lang)}</h3>
        <p className="text-xs text-stone-400">{t('settings.advanced_hint', lang)}</p>
        <button type="button" className="btn-secondary w-full text-sm" onClick={confirmRefresh} disabled={refreshMut.isPending}>
          {t('settings.refresh_pnl', lang)}
        </button>
        <button type="button" className="btn-secondary w-full text-sm text-red-700" onClick={confirmReset} disabled={resetMut.isPending}>
          {t('settings.reset', lang)}
        </button>
        {maintMsg && <p className="text-sm text-green-600">{maintMsg}</p>}
      </div>
    </div>
  )
}
