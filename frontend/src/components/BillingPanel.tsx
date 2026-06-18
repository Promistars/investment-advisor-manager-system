import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { useEffect, useState } from 'react'
import { useAuth } from '../context/AuthContext'
import { api, type BillingState } from '../lib/api'
import { fmtMoney } from '../lib/format'
import { t, e } from '../lib/i18n'

export function BillingPanel({ account }: { account: string }) {
  const { prefs } = useAuth()
  const lang = prefs.lang
  const qc = useQueryClient()
  const [mode, setMode] = useState<'pct' | 'asset'>('pct')
  const [targetPct, setTargetPct] = useState(20)
  const [targetAsset, setTargetAsset] = useState(0)
  const [feeRatio, setFeeRatio] = useState(20)
  const [manualDate, setManualDate] = useState('')
  const [manualFee, setManualFee] = useState(0)
  const [showManual, setShowManual] = useState(false)

  const body = {
    target_mode: mode,
    target_pct: targetPct,
    target_asset: mode === 'asset' ? targetAsset : null,
    fee_ratio: feeRatio,
  }

  const { data: state } = useQuery({
    queryKey: ['billing', account, body],
    queryFn: () => api.billingPreview(account, body),
  })

  useEffect(() => {
    if (!state) return
    const s = state as BillingState
    if (s.target_pct) setTargetPct(s.target_pct)
    if (s.fee_ratio) setFeeRatio(s.fee_ratio)
  }, [state?.target_pct, state?.fee_ratio])

  const exec = useMutation({
    mutationFn: (payload: { action: string; manual_date?: string; manual_fee?: number }) =>
      api.billingExecute(account, { ...body, ...payload }),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['admin', account] }),
  })

  const histPreview = useMutation({
    mutationFn: () => api.billingHistoricalPreview(account, { ...body, manual_date: manualDate }),
    onSuccess: (d) => {
      if (d.hist_fee != null) setManualFee(Number(d.hist_fee))
    },
  })

  if (!state) return null
  const s = state as BillingState
  const gap = Math.max(0, s.target_asset - s.current_asset)
  const progress = s.target_asset > 0 ? Math.min(100, (s.current_asset / s.target_asset) * 100) : 0

  return (
    <div className="card p-5 space-y-4">
      <h3 className="font-bold text-brand-700">{e('billing.title', lang, '💰', prefs.show_emoji)}</h3>

      <div className="rounded-xl border border-brand-100 bg-gradient-to-br from-brand-50/80 to-white p-4 space-y-3">
        <div className="flex flex-wrap items-start justify-between gap-3">
          <div>
            <div className="text-xs text-stone-500">{t('billing.current_asset', lang)}</div>
            <div className="text-2xl font-bold text-stone-800">{fmtMoney(s.current_asset, prefs)}</div>
          </div>
          <span
            className={`text-xs font-semibold px-2.5 py-1 rounded-full ${
              s.reached ? 'bg-green-100 text-green-800' : 'bg-amber-100 text-amber-800'
            }`}
          >
            {s.reached ? t('billing.status_reached', lang) : t('billing.status_pending', lang)}
          </span>
        </div>
        <div className="grid sm:grid-cols-2 gap-3 text-sm">
          <div>
            <div className="text-xs text-stone-500">{t('billing.target_label', lang)}</div>
            <div className="font-semibold">{fmtMoney(s.target_asset, prefs)}</div>
          </div>
          <div>
            <div className="text-xs text-stone-500">{t('billing.watermark', lang)}</div>
            <div className="font-semibold">{fmtMoney(s.adjusted_watermark, prefs)}</div>
          </div>
        </div>
        {!s.reached && (
          <div className="text-sm text-stone-600">
            {s.period_profit > 0 ? (
              <>
                {t('billing.gap_to_target', lang)}: <b className="text-brand-700">{fmtMoney(gap, prefs)}</b>
              </>
            ) : (
              t('billing.no_fee', lang)
            )}
          </div>
        )}
        <div>
          <div className="flex justify-between text-xs text-stone-500 mb-1">
            <span>{t('billing.progress', lang)}</span>
            <span>{progress.toFixed(1)}%</span>
          </div>
          <div className="h-2 rounded-full bg-stone-100 overflow-hidden">
            <div
              className={`h-full rounded-full transition-all ${s.reached ? 'bg-green-500' : 'bg-brand-500'}`}
              style={{ width: `${progress}%` }}
            />
          </div>
        </div>
      </div>

      <div className="flex flex-wrap gap-3">
        <label className="flex items-center gap-2 text-sm">
          <input type="radio" checked={mode === 'pct'} onChange={() => setMode('pct')} /> {t('billing.mode_pct', lang)}
        </label>
        <label className="flex items-center gap-2 text-sm">
          <input type="radio" checked={mode === 'asset'} onChange={() => setMode('asset')} /> {t('billing.mode_asset', lang)}
        </label>
      </div>
      <div className="grid sm:grid-cols-3 gap-3">
        {mode === 'pct' ? (
          <div>
            <label className="text-xs text-stone-500">{t('billing.target_pct', lang)}</label>
            <input type="number" className="input mt-1" value={targetPct} onChange={(e) => setTargetPct(Number(e.target.value))} />
          </div>
        ) : (
          <div>
            <label className="text-xs text-stone-500">{t('billing.target_asset', lang)}</label>
            <input type="number" className="input mt-1" value={targetAsset || s.target_asset} onChange={(e) => setTargetAsset(Number(e.target.value))} />
          </div>
        )}
        <div>
          <label className="text-xs text-stone-500">{t('billing.fee_ratio', lang)}</label>
          <input type="number" className="input mt-1" value={feeRatio} onChange={(e) => setFeeRatio(Number(e.target.value))} />
        </div>
      </div>
      <div className={`rounded-xl p-3 text-sm ${s.reached ? 'bg-green-50 text-green-800' : 'bg-stone-50 text-stone-600'}`}>
        {s.reached ? (
          <>
            {t('billing.reached', lang, { fee: fmtMoney(s.fee_amount, prefs), extra: fmtMoney(s.extra_profit, prefs) })}
            <div className="flex gap-2 mt-3">
              <button type="button" className="btn-primary text-xs flex-1" onClick={() => exec.mutate({ action: 'internal' })}>
                {t('billing.internal', lang)}
              </button>
              <button type="button" className="btn-secondary text-xs flex-1" onClick={() => exec.mutate({ action: 'external' })}>
                {t('billing.external', lang)}
              </button>
            </div>
          </>
        ) : s.period_profit > 0 ? (
          <>{t('billing.profit_gap', lang, { gap: fmtMoney(gap, prefs) })}</>
        ) : (
          <>{t('billing.no_fee', lang)}</>
        )}
      </div>
      <button type="button" className="text-sm text-brand-600" onClick={() => setShowManual(!showManual)}>
        {showManual ? t('billing.manual_toggle_hide', lang) : t('billing.manual_toggle_show', lang)} {t('billing.manual_title', lang)}
      </button>
      {showManual && (
        <div className="border border-stone-100 rounded-xl p-3 space-y-2">
          <input type="date" className="input" value={manualDate} onChange={(e) => setManualDate(e.target.value)} />
          <button type="button" className="btn-secondary text-xs" onClick={() => histPreview.mutate()} disabled={!manualDate}>
            {t('billing.manual_preview', lang)}
          </button>
          <input type="number" className="input" value={manualFee} onChange={(e) => setManualFee(Number(e.target.value))} />
          <div className="flex gap-2">
            <button type="button" className="btn-primary text-xs flex-1" onClick={() => exec.mutate({ action: 'manual_internal', manual_date: manualDate, manual_fee: manualFee })}>
              {t('billing.manual_internal', lang)}
            </button>
            <button type="button" className="btn-secondary text-xs flex-1" onClick={() => exec.mutate({ action: 'manual_external', manual_date: manualDate, manual_fee: manualFee })}>
              {t('billing.manual_external', lang)}
            </button>
          </div>
        </div>
      )}
      {(s.billing_history?.length ?? 0) > 0 && (
        <div>
          <h4 className="font-medium mb-2">{t('billing.history', lang)}</h4>
          <table className="w-full text-xs">
            <thead>
              <tr className="text-stone-500 border-b">
                <th className="text-left py-1">{t('ledger.col_date', lang)}</th>
                <th className="text-left py-1">{t('ledger.col_type', lang)}</th>
                <th className="text-left py-1">{t('billing.watermark', lang)}</th>
                <th className="text-left py-1">{t('ledger.col_amount', lang)}</th>
              </tr>
            </thead>
            <tbody>
              {s.billing_history.map((r) => (
                <tr key={`${r.date}-${r.type}`} className="border-b border-stone-50">
                  <td className="py-1">{r.date}</td>
                  <td className="py-1">{r.type}</td>
                  <td className="py-1">{fmtMoney(r.watermark, prefs)}</td>
                  <td className="py-1">{fmtMoney(r.fee_amount, prefs)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  )
}
