import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { useMemo, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { ExternalLink, Plus, Trash2 } from 'lucide-react'
import { api } from '../lib/api'
import { fmtMoney, fmtPct, pnlClass } from '../lib/format'
import { prefViewToApi } from '../lib/prefsNormalize'
import { t, e } from '../lib/i18n'
import { appPath } from '../lib/paths'
import { useAuth } from '../context/AuthContext'

export function HallPage() {
  const { prefs, user } = useAuth()
  const lang = prefs.lang
  const navigate = useNavigate()
  const qc = useQueryClient()
  const [newName, setNewName] = useState('')
  const [confirmDelete, setConfirmDelete] = useState<string | null>(null)

  const { data: accounts = [], isLoading } = useQuery({
    queryKey: ['accounts'],
    queryFn: api.accounts,
  })

  const { data: feeTotal } = useQuery({
    queryKey: ['fee-total'],
    queryFn: api.feeTotal,
  })

  const totalFees = useMemo(() => {
    if (feeTotal != null) return feeTotal.total_fees
    return accounts.reduce((sum, a) => sum + (a.fees_collected ?? 0), 0)
  }, [feeTotal, accounts])

  const accountCount = feeTotal?.account_count ?? accounts.length

  const feeBreakdown = useMemo(
    () =>
      [...accounts]
        .map((a) => ({ name: a.name, fees: a.fees_collected ?? 0 }))
        .filter((x) => x.fees > 0)
        .sort((a, b) => b.fees - a.fees),
    [accounts],
  )

  const createMut = useMutation({
    mutationFn: (name: string) => api.createAccount(name),
    onSuccess: (_data, name) => {
      qc.invalidateQueries({ queryKey: ['accounts'] })
      navigate(`/account/${encodeURIComponent(name)}`)
    },
  })

  const deleteMut = useMutation({
    mutationFn: (name: string) => api.deleteAccount(name),
    onSuccess: () => {
      setConfirmDelete(null)
      qc.invalidateQueries({ queryKey: ['accounts'] })
    },
  })

  const defaultView = prefViewToApi(prefs.default_view)

  return (
    <div>
      <h2 className="text-2xl font-bold text-stone-800 mb-6">{e('hall.title', lang, '🏦', prefs.show_emoji)}</h2>

      {user && !isLoading && (
        <div className="relative overflow-hidden rounded-2xl border border-gold-300/50 bg-gradient-to-br from-white via-gold-50/30 to-brand-50/40 shadow-md mb-6">
          <div className="absolute inset-x-0 top-0 h-1 bg-gradient-to-r from-gold-500 via-gold-400 to-brand-500" />
          <div className="p-5 sm:p-6 flex flex-wrap items-end justify-between gap-4">
            <div>
              <div className="text-xs font-semibold tracking-widest text-gold-600 uppercase">{t('hall.total_fees', lang)}</div>
              <div className="text-3xl sm:text-4xl font-extrabold text-brand-700 mt-1 tabular-nums">{fmtMoney(totalFees, prefs)}</div>
              <p className="text-xs text-stone-500 mt-2 max-w-md">{t('hall.total_fees_sub', lang)}</p>
            </div>
            {accountCount > 0 && (
              <div className="text-right text-sm text-stone-500">
                <span className="font-semibold text-stone-700">{accountCount}</span>
                {lang === 'zh' ? ' 个专户' : ' accounts'}
              </div>
            )}
          </div>
          <div className="border-t border-gold-200/40 px-5 sm:px-6 py-4 bg-white/40">
            <div className="text-xs font-semibold text-stone-500 mb-2">{t('hall.fees_by_account', lang)}</div>
            {feeBreakdown.length === 0 ? (
              <p className="text-xs text-stone-400">{t('hall.fees_none', lang)}</p>
            ) : (
              <ul className="space-y-1.5">
                {feeBreakdown.map((row) => (
                  <li key={row.name} className="flex items-center justify-between gap-4 text-sm">
                    <span className="text-stone-700 truncate">{row.name}</span>
                    <span className="font-semibold text-brand-700 tabular-nums shrink-0">{fmtMoney(row.fees, prefs)}</span>
                  </li>
                ))}
              </ul>
            )}
          </div>
        </div>
      )}

      <div className="grid lg:grid-cols-3 gap-6">
        <div className="lg:col-span-2 space-y-4">
          {isLoading && <p className="text-stone-500">{t('common.loading', lang)}</p>}
          {!isLoading && accounts.length === 0 && (
            <div className="card p-8 text-center text-stone-500">{t('hall.empty', lang)}</div>
          )}
          {accounts.map((acc) => (
            <div key={acc.name} className="card p-5 flex flex-col sm:flex-row sm:items-center gap-4">
              <div className="flex-1 min-w-0">
                <h3 className="text-lg font-semibold text-stone-800">{acc.name}</h3>
                <p className={`text-xl font-bold mt-1 ${pnlClass(acc.pnl, prefs)}`}>
                  {fmtMoney(acc.pnl, prefs)} ({fmtPct(acc.pnl_pct)})
                </p>
                <p className="text-xs text-stone-400 mt-1">
                  {acc.last_accessed ? `${t('hall.last_access', lang)}: ${acc.last_accessed}` : ''}
                  {acc.as_of_date ? ` · ${t('hall.as_of', lang, { date: acc.as_of_date })}` : ''}
                </p>
              </div>
              <div className="flex gap-2 shrink-0">
                {confirmDelete === acc.name ? (
                  <div className="flex flex-col gap-2 sm:items-end">
                    <p className="text-xs text-red-700 max-w-xs">{t('hall.delete_confirm', lang, { name: acc.name }).replace(/\*\*/g, '')}</p>
                    <div className="flex gap-2">
                    <button type="button" className="btn-primary" onClick={() => deleteMut.mutate(acc.name)}>
                      {t('hall.delete_yes', lang)}
                    </button>
                    <button type="button" className="btn-secondary" onClick={() => setConfirmDelete(null)}>
                      {t('hall.delete_no', lang)}
                    </button>
                    </div>
                  </div>
                ) : (
                  <>
                    <button
                      type="button"
                      className="btn-primary"
                      onClick={() => {
                        api.touchAccount(acc.name).catch(() => {})
                        navigate(`/account/${encodeURIComponent(acc.name)}`)
                      }}
                    >
                      {t('hall.enter', lang)} →
                    </button>
                    {user && (
                      <a
                        href={appPath(
                          `/client/${encodeURIComponent(user)}/${encodeURIComponent(acc.name)}?lang=${prefs.lang}&view=${defaultView}`,
                        )}
                        target="_blank"
                        rel="noreferrer"
                        className="btn-secondary text-xs inline-flex items-center gap-1"
                        title={t('hall.client_preview', lang)}
                      >
                        <ExternalLink size={14} />
                      </a>
                    )}
                    <button
                      type="button"
                      className="btn-secondary px-3"
                      onClick={() => setConfirmDelete(acc.name)}
                      aria-label={t('hall.delete', lang)}
                    >
                      <Trash2 size={16} />
                    </button>
                  </>
                )}
              </div>
            </div>
          ))}
        </div>
        <div className="card p-5 h-fit">
          <h3 className="font-semibold text-stone-800 mb-4 flex items-center gap-2">
            <Plus size={18} /> {t('hall.create_title', lang)}
          </h3>
          <input
            className="input mb-3"
            placeholder={t('hall.create_ph', lang)}
            value={newName}
            onChange={(e) => setNewName(e.target.value)}
          />
          <button
            type="button"
            className="btn-primary w-full"
            disabled={!newName.trim() || createMut.isPending}
            onClick={() => {
              createMut.mutate(newName.trim())
              setNewName('')
            }}
          >
            {t('hall.create_btn', lang)}
          </button>
        </div>
      </div>
    </div>
  )
}
