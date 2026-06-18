import type { UserPrefs } from '../lib/api'
import { fmtMoney, fmtPct, pnlClass } from '../lib/format'
import { t } from '../lib/i18n'

interface Props {
  kpi: {
    period_return: number
    benchmark_level: number
    benchmark_return: number
    alpha: number
    total_asset: number
    max_drawdown: number
    sharpe_ratio: number
  }
  benchmark: string
  prefs: UserPrefs
}

function KpiCard({
  label,
  value,
  sub,
  valueClass,
}: {
  label: string
  value: string
  sub?: string
  valueClass?: string
}) {
  return (
    <div className="card relative overflow-hidden p-5">
      <div className="absolute inset-x-0 top-0 h-0.5 bg-gradient-to-r from-gold-500 to-brand-500" />
      <div className="text-xs font-medium text-stone-500 mb-2">{label}</div>
      <div className={`text-2xl font-bold tracking-tight ${valueClass ?? 'text-stone-800'}`}>{value}</div>
      {sub && <div className="text-xs text-stone-400 mt-1">{sub}</div>}
    </div>
  )
}

export function KpiGrid({ kpi, benchmark, prefs }: Props) {
  const lang = prefs.lang
  return (
    <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
      <KpiCard
        label={t('kpi.period_return', lang)}
        value={fmtPct(kpi.period_return)}
        valueClass={pnlClass(kpi.period_return, prefs)}
      />
      <KpiCard
        label={t('kpi.benchmark', lang, { name: benchmark })}
        value={fmtMoney(kpi.benchmark_level, prefs)}
        sub={fmtPct(kpi.benchmark_return)}
      />
      <KpiCard
        label={t('kpi.alpha', lang)}
        value={fmtPct(kpi.alpha)}
        valueClass={pnlClass(kpi.alpha, prefs)}
      />
      <KpiCard label={t('kpi.total_asset', lang)} value={fmtMoney(kpi.total_asset, prefs)} />
      <KpiCard label={t('kpi.max_dd', lang)} value={fmtPct(kpi.max_drawdown, false)} valueClass="text-brand-600" />
      <KpiCard label={t('kpi.sharpe', lang)} value={Number.isFinite(kpi.sharpe_ratio) ? kpi.sharpe_ratio.toFixed(2) : '—'} />
    </div>
  )
}
