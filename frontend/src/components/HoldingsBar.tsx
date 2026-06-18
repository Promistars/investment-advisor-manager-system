import { useState } from 'react'
import { useAuth } from '../context/AuthContext'
import { fmtMoney } from '../lib/format'
import { t } from '../lib/i18n'

const COLORS = ['#34D399', '#60A5FA', '#818CF8', '#A78BFA', '#F472B6', '#FBBF24', '#22D3EE']

export function HoldingsBar({
  items,
  asOf,
}: {
  items: Array<{ name: string; value: number; shares: number; pct: number }>
  asOf: string
}) {
  const { prefs } = useAuth()
  const lang = prefs.lang
  const [hoverIdx, setHoverIdx] = useState<number | null>(null)

  if (!items.length) return <p className="text-stone-500 text-sm">{t('admin.holdings_empty', lang)}</p>

  const hovered = hoverIdx != null ? items[hoverIdx] : null

  return (
    <div className="relative">
      <h3 className="font-semibold text-stone-800 mb-3">{t('admin.holdings_title', lang, { date: asOf })}</h3>
      <div className="flex flex-wrap justify-center gap-4 mb-3">
        {items.map((it, i) => (
          <div key={it.name} className="flex items-center gap-1.5 text-xs text-stone-600">
            <span className="w-3 h-3 rounded-sm" style={{ background: COLORS[i % COLORS.length] }} />
            {it.name}
          </div>
        ))}
      </div>
      <div
        className="relative flex h-10 rounded-full overflow-hidden shadow-sm cursor-default"
        onMouseLeave={() => setHoverIdx(null)}
      >
        {items.map((it, i) => (
          <div
            key={it.name}
            className={`flex items-center justify-center text-white text-xs font-semibold transition-opacity ${hoverIdx != null && hoverIdx !== i ? 'opacity-60' : ''}`}
            style={{ width: `${it.pct}%`, background: COLORS[i % COLORS.length], minWidth: it.pct > 3 ? undefined : '0.5rem' }}
            onMouseEnter={() => setHoverIdx(i)}
          >
            {it.pct >= 8 ? `${it.pct.toFixed(2)}%` : ''}
          </div>
        ))}
      </div>
      {hovered && (
        <div className="absolute left-1/2 -translate-x-1/2 top-full mt-2 z-20 min-w-[10rem] rounded-xl bg-stone-900 text-white text-xs px-3 py-2 shadow-lg pointer-events-none">
          <div className="font-semibold mb-1">{hovered.name}</div>
          <div>{t('holdings.value', lang)}: {fmtMoney(hovered.value, prefs)}</div>
          <div>{hovered.pct.toFixed(2)}%</div>
          {hovered.shares > 0 && (
            <div>{t('holdings.shares', lang)}: {hovered.shares.toLocaleString(lang === 'zh' ? 'zh-CN' : 'en-US')}</div>
          )}
        </div>
      )}
    </div>
  )
}
