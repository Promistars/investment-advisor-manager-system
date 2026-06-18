import { useState } from 'react'
import { ChevronDown, ChevronUp, Save, Trash2 } from 'lucide-react'
import { useAuth } from '../context/AuthContext'
import type { AdminMeta, TradeRow } from '../lib/api'
import { fmtCell, fmtMoney, fmtPct, pnlClass, round2 } from '../lib/format'
import { t, txLabel } from '../lib/i18n'

const TX_TYPES = ['转入本金', '提取现金', '买入股票', '卖出股票', '提取管理费(内扣)', '结账重置(外付)']
const PREVIEW_ROWS = 5

function ExpandBar({
  expanded,
  total,
  onToggle,
  lang,
}: {
  expanded: boolean
  total: number
  onToggle: () => void
  lang: 'zh' | 'en'
}) {
  if (total <= PREVIEW_ROWS) return null
  return (
    <button type="button" className="btn-secondary w-full text-xs mt-3 inline-flex items-center justify-center gap-1" onClick={onToggle}>
      {expanded ? (
        <>
          <ChevronUp size={14} /> {t('common.collapse', lang)}
        </>
      ) : (
        <>
          <ChevronDown size={14} /> {t('common.expand_all', lang)} ({total})
        </>
      )}
    </button>
  )
}

function LedgerNumInput({
  value,
  width,
  onChange,
  onBlurRound,
}: {
  value: number | null
  width: string
  onChange: (v: number | null) => void
  onBlurRound: (v: number) => void
}) {
  return (
    <input
      type="number"
      step="0.01"
      className={`input py-0.5 ${width}`}
      value={value ?? ''}
      onChange={(e) => onChange(e.target.value ? Number(e.target.value) : null)}
      onBlur={(e) => {
        if (e.target.value) onBlurRound(round2(Number(e.target.value)))
      }}
    />
  )
}

export function RadarPanel({ admin }: { admin: AdminMeta }) {
  const { prefs } = useAuth()
  const lang = prefs.lang
  return (
    <div className="card p-4 space-y-3">
      <h3 className="font-semibold">{t('admin.radar', lang)}</h3>
      <p className="text-xs text-stone-400">{t('admin.radar_asof', lang, { date: admin.snap_date }).replace(/\*\*/g, '')}</p>

      <div className="rounded-xl bg-brand-50/60 border border-brand-100 p-3">
        <div className="text-xs text-stone-500">{t('admin.radar_total_asset', lang)}</div>
        <div className="text-xl font-bold text-brand-700">{fmtMoney(admin.total_asset, prefs)}</div>
        <div className={`text-sm font-medium mt-1 ${pnlClass(admin.unrealized_pnl, prefs)}`}>
          {t('admin.radar_unrealized', lang)}: {fmtMoney(admin.unrealized_pnl, prefs)} ({fmtPct(admin.return_pct)})
        </div>
      </div>

      <div className="grid grid-cols-2 gap-2 text-sm">
        <div className="rounded-lg bg-stone-50 p-2.5">
          <div className="text-xs text-stone-500">{t('admin.cash_avail', lang)}</div>
          <div className="font-semibold">{fmtMoney(admin.cash, prefs)}</div>
          <div className="text-xs text-stone-400">{admin.cash_pct.toFixed(1)}%</div>
        </div>
        <div className="rounded-lg bg-stone-50 p-2.5">
          <div className="text-xs text-stone-500">{t('admin.radar_stock_pct', lang)}</div>
          <div className="font-semibold">{admin.stock_pct.toFixed(1)}%</div>
          <div className="text-xs text-stone-400">{admin.position_count} {t('admin.radar_positions', lang)}</div>
        </div>
        <div className="rounded-lg bg-stone-50 p-2.5">
          <div className="text-xs text-stone-500">{t('admin.metric_principal', lang)}</div>
          <div className="font-semibold">{fmtMoney(admin.engine_principal, prefs)}</div>
        </div>
        <div className="rounded-lg bg-stone-50 p-2.5">
          <div className="text-xs text-stone-500">{t('admin.radar_nav', lang)}</div>
          <div className="font-semibold">{admin.nav.toFixed(4)}</div>
        </div>
        <div className="rounded-lg bg-stone-50 p-2.5">
          <div className="text-xs text-stone-500">{t('admin.metric_fees', lang)}</div>
          <div className="font-semibold text-brand-600">-{fmtMoney(admin.fees, prefs)}</div>
        </div>
        <div className="rounded-lg bg-stone-50 p-2.5">
          <div className="text-xs text-stone-500">{t('admin.radar_trades', lang)}</div>
          <div className="font-semibold">{admin.trade_count}</div>
        </div>
      </div>

      <p className="text-xs text-stone-400">
        {t('ledger.ledger_note', lang, {
          in: fmtMoney(admin.ledger_in, prefs),
          out: fmtMoney(admin.ledger_out, prefs),
          net: fmtMoney(admin.ledger_net, prefs),
        })}
      </p>
      {admin.principal_mismatch && (
        <p className="text-xs text-amber-700 bg-amber-50 rounded-lg p-2">{t('ledger.principal_warn', lang)}</p>
      )}
    </div>
  )
}

export function LedgerEditor({
  trades,
  stockNames,
  onChange,
  onSave,
  saving,
}: {
  trades: TradeRow[]
  stockNames: string[]
  onChange: (rows: TradeRow[]) => void
  onSave: () => void
  saving: boolean
}) {
  const { prefs } = useAuth()
  const lang = prefs.lang
  const [selected, setSelected] = useState<number[]>([])
  const [expanded, setExpanded] = useState(false)

  const toggle = (i: number) => setSelected((s) => (s.includes(i) ? s.filter((x) => x !== i) : [...s, i]))
  const visibleCount = expanded ? trades.length : Math.min(PREVIEW_ROWS, trades.length)
  const visibleTrades = trades.slice(0, visibleCount)

  return (
    <div className="card p-4 overflow-x-auto">
      <div className="flex flex-wrap items-center justify-between gap-2 mb-3">
        <h3 className="font-semibold">{t('admin.ledger', lang)}</h3>
        <div className="flex gap-2 flex-wrap">
          <button
            type="button"
            className="btn-secondary text-xs"
            onClick={() =>
              onChange([
                ...trades,
                { 日期: new Date().toISOString().slice(0, 10), 操作类型: '转入本金', 标的: '', '数量(股)': null, '成交单价(¥)': null, '实际结算总金额(¥)': 10000 },
              ])
            }
          >
            {t('ledger.add_row', lang)}
          </button>
          <button
            type="button"
            className="btn-secondary text-xs text-red-700"
            disabled={!selected.length}
            onClick={() => onChange(trades.filter((_, i) => !selected.includes(i)))}
          >
            <Trash2 size={14} className="inline" /> {t('ledger.del_selected', lang)}
          </button>
          <button type="button" className="btn-primary text-xs" onClick={onSave} disabled={saving}>
            <Save size={14} className="inline" /> {t('admin.ledger_save', lang)}
          </button>
        </div>
      </div>
      <table className="w-full text-xs">
        <thead>
          <tr className="text-stone-500 border-b">
            <th className="py-1 w-8" />
            <th>{t('ledger.col_date', lang)}</th>
            <th>{t('ledger.col_type', lang)}</th>
            <th>{t('ledger.col_symbol', lang)}</th>
            <th>{t('ledger.col_qty', lang)}</th>
            <th>{t('ledger.col_price', lang)}</th>
            <th>{t('ledger.col_amount', lang)}</th>
          </tr>
        </thead>
        <tbody>
          {visibleTrades.map((row, i) => (
            <tr key={`${row.日期}-${row.操作类型}-${i}`} className="border-b border-stone-50">
              <td><input type="checkbox" checked={selected.includes(i)} onChange={() => toggle(i)} /></td>
              <td><input className="input py-0.5 w-24" value={row.日期} onChange={(e) => { const n = [...trades]; n[i] = { ...row, 日期: e.target.value }; onChange(n) }} /></td>
              <td>
                <select className="input py-0.5" value={row.操作类型} onChange={(e) => { const n = [...trades]; n[i] = { ...row, 操作类型: e.target.value }; onChange(n) }}>
                  {TX_TYPES.map((tx) => (
                    <option key={tx} value={tx}>
                      {txLabel(tx, lang)}
                    </option>
                  ))}
                </select>
              </td>
              <td>
                <select className="input py-0.5 w-20" value={row.标的 ?? ''} onChange={(e) => { const n = [...trades]; n[i] = { ...row, 标的: e.target.value }; onChange(n) }}>
                  <option value="" />
                  {stockNames.map((s) => <option key={s}>{s}</option>)}
                </select>
              </td>
              <td>
                <LedgerNumInput
                  width="w-16"
                  value={row['数量(股)']}
                  onChange={(v) => { const n = [...trades]; n[i] = { ...row, '数量(股)': v }; onChange(n) }}
                  onBlurRound={(v) => { const n = [...trades]; n[i] = { ...row, '数量(股)': v }; onChange(n) }}
                />
              </td>
              <td>
                <LedgerNumInput
                  width="w-16"
                  value={row['成交单价(¥)']}
                  onChange={(v) => { const n = [...trades]; n[i] = { ...row, '成交单价(¥)': v }; onChange(n) }}
                  onBlurRound={(v) => { const n = [...trades]; n[i] = { ...row, '成交单价(¥)': v }; onChange(n) }}
                />
              </td>
              <td>
                <LedgerNumInput
                  width="w-20"
                  value={row['实际结算总金额(¥)']}
                  onChange={(v) => { const n = [...trades]; n[i] = { ...row, '实际结算总金额(¥)': v }; onChange(n) }}
                  onBlurRound={(v) => { const n = [...trades]; n[i] = { ...row, '实际结算总金额(¥)': v }; onChange(n) }}
                />
              </td>
            </tr>
          ))}
        </tbody>
      </table>
      {!expanded && trades.length > PREVIEW_ROWS && (
        <p className="text-xs text-stone-400 mt-2 text-center">{t('common.rows_hidden', lang, { n: trades.length - PREVIEW_ROWS })}</p>
      )}
      <ExpandBar expanded={expanded} total={trades.length} onToggle={() => setExpanded((v) => !v)} lang={lang} />
      <p className="text-xs text-stone-400 mt-2">{t('common.total_rows', lang, { n: trades.length })}</p>
    </div>
  )
}

export function StatementTable({ rows }: { rows: Array<Record<string, unknown>> }) {
  const { prefs } = useAuth()
  const lang = prefs.lang
  const [expanded, setExpanded] = useState(false)
  if (!rows.length) return null
  const cols = Object.keys(rows[0])
  const visibleCount = expanded ? rows.length : Math.min(PREVIEW_ROWS, rows.length)
  const visibleRows = rows.slice(0, visibleCount)

  return (
    <div className="card p-4 overflow-x-auto mt-4">
      <h4 className="font-medium mb-2">{t('ledger.statement_title', lang)}</h4>
      <table className="w-full text-xs whitespace-nowrap">
        <thead>
          <tr className="text-stone-500 border-b">{cols.map((c) => <th key={c} className="text-left py-1 pr-3">{c}</th>)}</tr>
        </thead>
        <tbody>
          {visibleRows.map((row, i) => (
            <tr key={i} className="border-b border-stone-50">
              {cols.map((c) => (
                <td key={c} className="py-1 pr-3 tabular-nums">{fmtCell(row[c], lang)}</td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
      {!expanded && rows.length > PREVIEW_ROWS && (
        <p className="text-xs text-stone-400 mt-2 text-center">{t('common.rows_hidden', lang, { n: rows.length - PREVIEW_ROWS })}</p>
      )}
      <ExpandBar expanded={expanded} total={rows.length} onToggle={() => setExpanded((v) => !v)} lang={lang} />
    </div>
  )
}
