import { useQuery } from '@tanstack/react-query'
import { useEffect, useState } from 'react'
import { useLocation, useParams, useSearchParams } from 'react-router-dom'
import { AssetChart, ReturnChart } from '../components/Charts'
import { KpiGrid } from '../components/KpiGrid'
import { api, type UserPrefs } from '../lib/api'
import { fmtDate, fmtMoney, pnlColorsForLang } from '../lib/format'
import { t, viewLabels } from '../lib/i18n'

const guestPrefs: UserPrefs = {
  lang: 'zh',
  pnl_colors: 'cn',
  date_format: 'iso',
  compact_ui: false,
  show_emoji: true,
  default_view: 'month',
}

export function ClientPage() {
  const { username = '', accountName = '' } = useParams()
  const user = decodeURIComponent(username)
  const account = decodeURIComponent(accountName)
  const [params] = useSearchParams()
  const location = useLocation()
  const viewParam = params.get('view') || 'monthly'
  const [view, setView] = useState(viewParam)
  const [tab, setTab] = useState<'return' | 'asset'>('return')
  const [customStart, setCustomStart] = useState('')
  const [customEnd, setCustomEnd] = useState('')

  useEffect(() => {
    setView(params.get('view') || 'monthly')
  }, [params, location.key])

  const lang = params.get('lang') === 'en' ? 'en' : 'zh'
  const prefs: UserPrefs = { ...guestPrefs, lang, pnl_colors: pnlColorsForLang(lang) }
  const custom = view === 'custom' && customStart && customEnd ? { start: customStart, end: customEnd } : undefined

  const { data, isLoading, isError, refetch } = useQuery({
    queryKey: ['client', user, account, view, custom?.start, custom?.end],
    queryFn: () => api.clientDashboard(user, account, view, custom),
    refetchOnMount: 'always',
  })

  if (isLoading) return <p className="text-stone-500 p-8">{t('common.loading', lang)}</p>
  if (isError || !data?.ok) {
    const msg =
      isError
        ? t('client.load_fail', lang)
        : data?.message === 'insufficient_data'
          ? t('client.insufficient', lang)
          : data?.message || t('client.no_data', lang)
    return (
      <div className="card p-8 text-center text-stone-500 max-w-lg mx-auto mt-8">
        <h2 className="text-lg font-semibold text-brand-700 mb-2">{t('client.title', lang)}</h2>
        <p>{msg}</p>
        <p className="text-xs mt-2 text-stone-400">{account}</p>
        {isError && (
          <button type="button" className="btn-secondary mt-4 text-sm" onClick={() => refetch()}>
            {t('common.retry', lang)}
          </button>
        )}
      </div>
    )
  }

  const maxDate = data.max_selectable_date || data.period_end

  return (
    <div className="space-y-6">
      <div>
        <p className="text-sm text-stone-400">{t('client.sub', lang, { acc: account })}</p>
        <h2 className="text-2xl font-bold text-brand-700">{t('client.title', lang)}</h2>
        <p className="text-sm text-stone-500 mt-1">
          {fmtDate(data.period_start, prefs)} — {fmtDate(data.period_end, prefs)}
        </p>
      </div>

      <div className="flex flex-wrap gap-2 no-print">
        {data.available_views.map((v) => (
          <button key={v} type="button" className={`rounded-full px-4 py-1.5 text-sm font-medium border ${view === v ? 'bg-brand-600 text-white border-brand-600' : 'bg-white border-stone-200'}`} onClick={() => setView(v)}>
            {viewLabels[v]?.[lang] ?? v}
          </button>
        ))}
      </div>

      {view === 'custom' && (
        <div className="flex flex-wrap gap-2 no-print">
          <input type="date" className="input w-auto" value={customStart} onChange={(e) => setCustomStart(e.target.value)} />
          <input type="date" className="input w-auto" value={customEnd} onChange={(e) => setCustomEnd(e.target.value)} max={maxDate} />
        </div>
      )}

      <div className="text-sm text-stone-500">
        <p>
          {t('analytics.period_inflow', lang)}: <b>{fmtMoney(data.kpi.period_net_inflow, prefs)}</b>
        </p>
        <p>
          {t('analytics.engine_principal', lang)}: <b>{fmtMoney(data.kpi.engine_principal, prefs)}</b>
        </p>
      </div>

      <KpiGrid kpi={data.kpi} benchmark={data.benchmark} prefs={prefs} />

      <div className="card p-4">
        <div className="flex gap-4 border-b border-stone-100 mb-4">
          {(['return', 'asset'] as const).map((k) => (
            <button key={k} type="button" className={`pb-2 text-sm font-medium border-b-2 ${tab === k ? 'border-brand-600 text-brand-700' : 'border-transparent text-stone-500'}`} onClick={() => setTab(k)}>
              {k === 'return' ? t('chart.tab_return', lang) : t('chart.tab_asset', lang)}
            </button>
          ))}
        </div>
        {tab === 'return' ? (
          <ReturnChart key={`return-${location.key}-${view}`} data={data.charts} prefs={prefs} />
        ) : (
          <AssetChart key={`asset-${location.key}-${view}`} data={data.charts} prefs={prefs} />
        )}
        <p className="text-xs text-stone-400 mt-3 no-print">{t('client.chart_note', lang)}</p>
      </div>

      {data.commentary?.html ? (
        <div className="card p-6">
          <h3 className="font-semibold mb-3">{data.commentary.period}</h3>
          <div className="prose prose-sm max-w-none" dangerouslySetInnerHTML={{ __html: data.commentary.html }} />
        </div>
      ) : (
        <p className="text-sm text-stone-400">{t('client.commentary_empty', lang)}</p>
      )}
    </div>
  )
}
