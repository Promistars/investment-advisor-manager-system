import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { useEffect, useMemo, useState } from 'react'
import { Link, useParams } from 'react-router-dom'
import { ArrowLeft, ExternalLink } from 'lucide-react'
import { ErrorBoundary } from '../components/ErrorBoundary'
import { AdminTimelineChart } from '../components/AdminTimelineChart'
import { TradeEntryForm } from '../components/AdminTools'
import { BillingPanel } from '../components/BillingPanel'
import { AssetChart, ReturnChart } from '../components/Charts'
import { CommentaryEditor, SharePanel } from '../components/CommentaryEditor'
import { HoldingsBar } from '../components/HoldingsBar'
import { KpiGrid } from '../components/KpiGrid'
import { LedgerEditor, RadarPanel, StatementTable } from '../components/LedgerPanel'
import { useAuth } from '../context/AuthContext'
import { api, type TradeRow } from '../lib/api'
import { fmtDate, fmtMoney } from '../lib/format'
import { prefViewToApi } from '../lib/prefsNormalize'
import { t, e, viewLabels } from '../lib/i18n'
import { appUrl } from '../lib/paths'

export function AnalyticsPage() {
  const { accountName = '' } = useParams()
  const account = decodeURIComponent(accountName)
  const { prefs, user } = useAuth()
  const lang = prefs.lang
  const qc = useQueryClient()
  const [view, setView] = useState(() => prefViewToApi(prefs.default_view))
  const [tab, setTab] = useState<'return' | 'asset'>('return')
  const [customStart, setCustomStart] = useState('')
  const [customEnd, setCustomEnd] = useState('')
  const [trades, setTrades] = useState<TradeRow[]>([])

  useEffect(() => {
    setView(prefViewToApi(prefs.default_view))
  }, [account, prefs.default_view])

  const custom = view === 'custom' && customStart && customEnd ? { start: customStart, end: customEnd } : undefined

  const { data, isLoading, error, refetch } = useQuery({
    queryKey: ['admin', account, view, custom?.start, custom?.end],
    queryFn: () => api.adminBundle(account, view, custom),
    enabled: !!account,
  })

  useEffect(() => {
    if (data?.trades) setTrades(data.trades)
  }, [data])

  const saveMut = useMutation({
    mutationFn: () => api.saveTrades(account, trades),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['admin', account] })
      qc.invalidateQueries({ queryKey: ['accounts'] })
    },
  })

  const rollbackMut = useMutation({
    mutationFn: (indices: number[]) => api.removeTradeIndices(account, indices),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['admin', account] })
      qc.invalidateQueries({ queryKey: ['accounts'] })
    },
  })

  const defaultView = prefViewToApi(prefs.default_view)

  const clientUrl = useMemo(() => {
    if (!user) return ''
    const q = new URLSearchParams({ lang: prefs.lang, view: defaultView })
    return appUrl(`/client/${encodeURIComponent(user)}/${encodeURIComponent(account)}?${q}`)
  }, [user, account, prefs.lang, defaultView])

  const legacyClientUrl = useMemo(() => {
    if (!user) return ''
    const viewMap: Record<string, string> = { monthly: 'month', quarterly: 'quarter', yearly: 'year' }
    return appUrl(
      `/?user=${encodeURIComponent(user)}&acc=${encodeURIComponent(account)}&lang=${prefs.lang}&view=${viewMap[defaultView] || 'month'}`,
    )
  }, [user, account, prefs.lang, defaultView])

  if (isLoading) return <p className="text-stone-500">{t('common.loading', lang)}</p>

  if (error || !data?.admin) {
    const msg = error instanceof Error ? error.message : data?.message || t('analytics.load_fail', lang)
    return (
      <div>
        <Link to="/" className="text-brand-600 text-sm inline-flex items-center gap-1 mb-4">
          <ArrowLeft size={16} /> {t('common.back', lang)}
        </Link>
        <div className="card p-6 text-stone-600">{msg}</div>
      </div>
    )
  }

  const admin = data.admin
  const metricsOk = data.ok === true && data.kpi && data.charts?.length
  const invalidIndices = admin.invalid_trade_indices ?? []

  return (
    <ErrorBoundary title={t('analytics.boundary_fail', lang)}>
      <div className={`-mx-6 lg:-mx-8 -mt-6 lg:-mt-8 ${prefs.compact_ui ? 'gap-4' : ''}`}>
        <div className="sticky top-0 z-30 no-print">
          <div className="relative overflow-hidden border-b border-brand-100/80 bg-white/95 backdrop-blur-md shadow-lg shadow-brand-900/5">
            <div className="h-1 bg-gradient-to-r from-gold-500 via-gold-400 to-brand-500" />
            <div className="px-6 lg:px-8 py-4 flex flex-wrap items-center justify-between gap-4">
              <div className="min-w-0">
                <Link
                  to="/"
                  className="text-brand-600 text-sm inline-flex items-center gap-1 mb-2 hover:text-brand-700 transition cursor-pointer"
                >
                  <ArrowLeft size={16} /> {t('nav.hall', lang)}
                </Link>
                <h2 className="text-2xl sm:text-3xl font-extrabold text-stone-800 tracking-tight truncate">{account}</h2>
                {metricsOk && (
                  <p className="text-sm text-stone-500 mt-1 flex items-center gap-2">
                    <span className="inline-block w-1.5 h-1.5 rounded-full bg-gold-500" />
                    {fmtDate(data.period_start!, prefs)} — {fmtDate(data.period_end!, prefs)}
                  </p>
                )}
              </div>
              <div className="flex flex-wrap gap-2 shrink-0">
                <a
                  href={clientUrl}
                  target="_blank"
                  rel="noreferrer"
                  className="btn-primary text-xs inline-flex items-center gap-1.5 shadow-md shadow-brand-600/15"
                >
                  <ExternalLink size={14} /> {t('hall.client_preview', lang)}
                </a>
              </div>
            </div>
          </div>
        </div>

        <div className={`space-y-6 px-6 lg:px-8 pt-6 ${prefs.compact_ui ? 'gap-4' : ''}`}>
        {invalidIndices.length > 0 && (
          <div className="card p-4 bg-red-50 border border-red-200 space-y-2">
            <p className="text-sm font-semibold text-red-800">{t('trade.rollback_title', lang)}</p>
            <p className="text-sm text-red-700">
              {t('trade.rollback_msg', lang, { rows: invalidIndices.map((i) => i + 1).join(', ') })}
            </p>
            <button
              type="button"
              className="btn-primary text-xs"
              disabled={rollbackMut.isPending}
              onClick={() => rollbackMut.mutate(invalidIndices)}
            >
              {t('trade.rollback_btn', lang)}
            </button>
          </div>
        )}

        <div className="space-y-6 min-w-0">
          <SharePanel clientUrl={clientUrl} legacyUrl={legacyClientUrl} lang={lang} />

          <div className="card p-4 border-brand-100">
            <h3 className="font-bold text-brand-700 mb-1">{e('analytics.client_preview_title', lang, '📈', prefs.show_emoji)}</h3>
            <p className="text-xs text-stone-500 mb-3">{t('analytics.client_preview_sub', lang)}</p>
            {!metricsOk ? (
              <p className="text-sm text-amber-700 bg-amber-50 rounded-lg p-3">
                {t('analytics.insufficient', lang, { msg: data.message || 'insufficient_data' })}
              </p>
            ) : (
              <>
                <div className="flex flex-wrap gap-2 no-print mb-4">
                  {(data.available_views || []).map((v) => (
                    <button
                      key={v}
                      type="button"
                      className={`rounded-full px-4 py-1.5 text-sm font-medium border transition ${
                        view === v ? 'bg-brand-600 text-white border-brand-600' : 'bg-white border-stone-200 text-stone-600'
                      }`}
                      onClick={() => setView(v)}
                    >
                      {viewLabels[v]?.[lang] ?? v}
                    </button>
                  ))}
                </div>
                {view === 'custom' && (
                  <div className="flex flex-wrap gap-2 mb-4">
                    <input type="date" className="input w-auto" value={customStart} onChange={(e) => setCustomStart(e.target.value)} min={admin.account_start} max={admin.global_max_date} />
                    <input type="date" className="input w-auto" value={customEnd} onChange={(e) => setCustomEnd(e.target.value)} min={admin.account_start} max={admin.global_max_date} />
                  </div>
                )}
                <div className="text-sm text-stone-500 space-y-1 mb-4">
                  <p>
                    {t('analytics.period_inflow', lang)}: <b>{fmtMoney(data.kpi!.period_net_inflow, prefs)}</b>
                  </p>
                  <p>
                    {t('analytics.engine_principal', lang)}: <b>{fmtMoney(data.kpi!.engine_principal, prefs)}</b>
                  </p>
                </div>
                <KpiGrid kpi={data.kpi!} benchmark={data.benchmark!} prefs={prefs} />
                <div className="mt-4">
                  <div className="flex gap-4 border-b border-stone-100 mb-4">
                    {(['return', 'asset'] as const).map((k) => (
                      <button key={k} type="button" className={`pb-2 text-sm font-medium border-b-2 ${tab === k ? 'border-brand-600 text-brand-700' : 'border-transparent text-stone-500'}`} onClick={() => setTab(k)}>
                        {k === 'return' ? t('chart.tab_return', lang) : t('chart.tab_asset', lang)}
                      </button>
                    ))}
                  </div>
                  {tab === 'return' ? (
                    <ReturnChart key="return" data={data.charts!} prefs={prefs} />
                  ) : (
                    <AssetChart key="asset" data={data.charts!} prefs={prefs} />
                  )}
                </div>
                {data.commentary?.html && (
                  <div className="mt-4 p-4 bg-stone-50 rounded-xl">
                    <h4 className="font-semibold mb-2">{data.commentary.period}</h4>
                    <div className="prose prose-sm max-w-none" dangerouslySetInnerHTML={{ __html: data.commentary.html }} />
                  </div>
                )}
              </>
            )}
          </div>

          <h3 className="text-lg font-bold text-stone-800">{e('analytics.admin_console', lang, '🧭', prefs.show_emoji)}</h3>
          <div className="grid lg:grid-cols-3 gap-6">
            <div className="lg:col-span-2 space-y-6">
              <TradeEntryForm account={account} admin={admin} onSaved={() => refetch()} />
              <HoldingsBar items={admin.holdings} asOf={admin.snap_date} />
              <div className="card p-4">
                <AdminTimelineChart timeline={admin.timeline} />
              </div>
              <BillingPanel account={account} />
            </div>
            <RadarPanel admin={admin} />
          </div>

          <LedgerEditor trades={trades} stockNames={admin.stock_names} onChange={setTrades} onSave={() => saveMut.mutate()} saving={saveMut.isPending} />
          <StatementTable rows={admin.statement} />
          <CommentaryEditor account={account} reportPeriods={admin.report_periods} />
        </div>
        </div>
      </div>
    </ErrorBoundary>
  )
}
