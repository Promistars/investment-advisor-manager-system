import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { ChevronDown } from 'lucide-react'
import { useEffect, useState } from 'react'
import { useAuth } from '../context/AuthContext'
import { api } from '../lib/api'
import { round2 } from '../lib/format'
import { TRADE_ENTRY_TYPES, t, txLabel } from '../lib/i18n'

function SearchableSelect({
  options,
  value,
  onChange,
  placeholder,
  noMatchLabel,
}: {
  options: string[]
  value: string
  onChange: (v: string) => void
  placeholder?: string
  noMatchLabel: string
}) {
  const [query, setQuery] = useState(value)
  const [open, setOpen] = useState(false)

  useEffect(() => {
    setQuery(value)
  }, [value])

  const term = query.trim().toLowerCase()
  const shown = term ? options.filter((o) => o.toLowerCase().includes(term)) : options

  const commit = () => {
    setOpen(false)
    if (options.includes(query)) onChange(query)
    else setQuery(value)
  }

  const pick = (s: string) => {
    onChange(s)
    setQuery(s)
    setOpen(false)
  }

  return (
    <div className="relative mt-1">
      <input
        className="input pr-9"
        value={query}
        placeholder={placeholder}
        onChange={(e) => {
          setQuery(e.target.value)
          setOpen(true)
        }}
        onFocus={() => setOpen(true)}
        onBlur={() => window.setTimeout(commit, 150)}
      />
      <button
        type="button"
        tabIndex={-1}
        aria-label={placeholder}
        className="absolute right-2 top-1/2 -translate-y-1/2 rounded-md p-0.5 text-stone-400 hover:text-stone-600 cursor-pointer"
        onMouseDown={(e) => {
          e.preventDefault()
          setOpen((v) => !v)
        }}
      >
        <ChevronDown size={16} className={open ? 'rotate-180 transition-transform' : 'transition-transform'} />
      </button>
      {open && (
        <ul className="absolute z-30 mt-1 max-h-56 w-full overflow-y-auto rounded-xl border border-brand-100 bg-white py-1 text-sm shadow-lg">
          {shown.length === 0 ? (
            <li className="px-3 py-2 text-stone-400">{noMatchLabel}</li>
          ) : (
            shown.map((s) => (
              <li key={s}>
                <button
                  type="button"
                  className={`w-full px-3 py-1.5 text-left cursor-pointer ${
                    s === value ? 'bg-brand-50 text-brand-700 font-medium' : 'hover:bg-brand-50'
                  }`}
                  onMouseDown={(e) => {
                    e.preventDefault()
                    pick(s)
                  }}
                >
                  {s}
                </button>
              </li>
            ))
          )}
        </ul>
      )}
    </div>
  )
}

export function AccountSidebar({ account }: { account: string }) {
  const { prefs } = useAuth()
  const lang = prefs.lang
  const qc = useQueryClient()
  const [startDate, setStartDate] = useState('')
  const [stockName, setStockName] = useState('')
  const [force, setForce] = useState(false)
  const [ingestFeedback, setIngestFeedback] = useState<{ type: 'success' | 'error' | 'info'; text: string } | null>(null)

  const { data: meta, isLoading } = useQuery({
    queryKey: ['start-date', account],
    queryFn: () => api.getStartDate(account),
    enabled: !!account,
  })

  const saveStart = useMutation({
    mutationFn: () => api.setStartDate(account, startDate),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['start-date', account] })
      qc.invalidateQueries({ queryKey: ['admin', account] })
    },
  })

  const ingest = useMutation({
    mutationFn: () => api.ingestStock(stockName.trim(), force),
    onSuccess: (data) => {
      setIngestFeedback({
        type: 'success',
        text: data.message || t('admin.stock_fetch_ok', lang),
      })
      setStockName('')
      qc.invalidateQueries({ queryKey: ['admin', account] })
    },
    onError: (err) => {
      const msg = err instanceof Error ? err.message : String(err)
      const exists = /already exists/i.test(msg)
      setIngestFeedback({
        type: exists ? 'info' : 'error',
        text: exists ? t('admin.stock_exists', lang, { name: stockName.trim() }) : msg,
      })
    },
  })

  useEffect(() => {
    setStockName('')
    setForce(false)
    setIngestFeedback(null)
    if (meta?.start_date) setStartDate(meta.start_date)
  }, [account, meta?.start_date])

  if (isLoading) {
    return <p className="px-4 py-2 text-xs text-stone-400">{t('admin.loading_meta', lang)}</p>
  }
  if (!meta) return null

  return (
    <div className="px-4 py-4 space-y-4 text-sm border-t border-brand-100 min-w-0">
      <p className="text-xs font-semibold text-brand-700 break-words leading-snug" title={account}>
        {t('admin.current_account', lang, { acc: account })}
      </p>
      <div className="min-w-0">
        <label className="font-medium text-stone-700 block mb-1 text-xs leading-snug break-words">{t('admin.start_date', lang)}</label>
        <p className="text-xs text-stone-400 mb-2 leading-relaxed break-words">{t('admin.start_date_help', lang).replace(/\*\*/g, '')}</p>
        <input
          type="date"
          className="input text-xs w-full min-w-0 max-w-full box-border"
          min={meta.global_min_date}
          max={meta.global_max_date}
          value={startDate}
          onChange={(e) => setStartDate(e.target.value)}
        />
        {startDate !== meta.start_date && (
          <button type="button" className="btn-primary w-full mt-2 text-xs px-2 py-2 whitespace-normal leading-snug" onClick={() => saveStart.mutate()}>
            {t('admin.save_start', lang)}
          </button>
        )}
      </div>
      <hr className="border-brand-100" />
      <div className="min-w-0">
        <label className="font-medium text-stone-700 block mb-1 text-xs leading-snug break-words">{t('admin.add_stock', lang)}</label>
        <input
          className="input mb-2 text-xs w-full min-w-0 max-w-full box-border"
          placeholder={t('admin.stock_ph', lang)}
          value={stockName}
          onChange={(e) => {
            setStockName(e.target.value)
            setIngestFeedback(null)
          }}
        />
        <label className="flex items-start gap-2 text-xs text-stone-500 mb-2 cursor-pointer">
          <input type="checkbox" className="mt-0.5 shrink-0" checked={force} onChange={(e) => setForce(e.target.checked)} />
          <span className="break-words leading-snug">{t('admin.stock_force', lang)}</span>
        </label>
        <button
          type="button"
          className="btn-primary w-full text-xs px-2 py-2.5 whitespace-normal leading-snug disabled:opacity-50"
          disabled={!stockName.trim() || ingest.isPending}
          onClick={() => ingest.mutate()}
        >
          {ingest.isPending ? t('admin.stock_fetching', lang) : t('admin.stock_fetch', lang)}
        </button>
        {ingestFeedback && (
          <p
            className={`mt-2 text-xs rounded-lg px-2.5 py-2 leading-snug break-words ${
              ingestFeedback.type === 'success'
                ? 'bg-green-50 text-green-800 border border-green-200'
                : ingestFeedback.type === 'info'
                  ? 'bg-sky-50 text-sky-800 border border-sky-200'
                  : 'bg-red-50 text-red-800 border border-red-200'
            }`}
            role="status"
          >
            {ingestFeedback.type === 'success' ? '✓ ' : ingestFeedback.type === 'error' ? '✕ ' : 'ℹ '}
            {ingestFeedback.text}
          </p>
        )}
      </div>
    </div>
  )
}

export function TradeEntryForm({
  account,
  admin,
  onSaved,
}: {
  account: string
  admin: { global_max_date: string; account_start: string; stock_names: string[]; last_trade_type: string }
  onSaved: () => void
}) {
  const { prefs } = useAuth()
  const lang = prefs.lang
  const [tDate, setTDate] = useState(admin.global_max_date)
  const [tType, setTType] = useState(admin.last_trade_type || TRADE_ENTRY_TYPES[0])
  const [asset, setAsset] = useState(admin.stock_names[0] || '')
  const [qty, setQty] = useState(100)
  const [price, setPrice] = useState(10)
  const [total, setTotal] = useState(100000)

  const isStock = tType === '买入股票' || tType === '卖出股票'

  const { data: sug } = useQuery({
    queryKey: ['price', account, asset, tDate],
    queryFn: () => api.suggestedPrice(account, asset, tDate),
    enabled: isStock && !!asset,
  })

  useEffect(() => {
    if (sug?.price && sug.price > 0) setPrice(sug.price)
  }, [sug?.price])

  useEffect(() => {
    if (isStock) setTotal(Math.round(qty * price * 100) / 100)
  }, [qty, price, isStock])

  const append = useMutation({
    mutationFn: () =>
      api.appendTrade(account, {
        日期: tDate,
        操作类型: tType,
        标的: isStock ? asset : '',
        数量股: isStock ? qty : null,
        成交单价: isStock ? price : null,
        实际结算总金额: total,
      }),
    onSuccess: onSaved,
  })

  return (
    <div className="card p-4">
      <h3 className="font-semibold mb-3">{t('admin.trade_entry', lang)}</h3>
      <div className="grid sm:grid-cols-2 gap-3">
        <div>
          <label className="text-xs text-stone-500">{t('admin.trade_date', lang)}</label>
          <input type="date" className="input mt-1" min={admin.account_start} max={admin.global_max_date} value={tDate} onChange={(e) => setTDate(e.target.value)} />
        </div>
        <div>
          <label className="text-xs text-stone-500">{t('admin.trade_type', lang)}</label>
          <select className="input mt-1" value={tType} onChange={(e) => setTType(e.target.value)}>
            {TRADE_ENTRY_TYPES.map((x) => (
              <option key={x} value={x}>
                {txLabel(x, lang)}
              </option>
            ))}
          </select>
        </div>
        {isStock && (
          <>
            <div>
              <label className="text-xs text-stone-500">{t('admin.trade_asset', lang)}</label>
              <SearchableSelect
                options={admin.stock_names}
                value={asset}
                onChange={setAsset}
                placeholder={t('admin.stock_search_ph', lang)}
                noMatchLabel={t('admin.stock_no_match', lang)}
              />
            </div>
            <div>
              <label className="text-xs text-stone-500">{t('admin.trade_qty', lang)}</label>
              <input type="number" className="input mt-1" min={1} step={100} value={qty} onChange={(e) => setQty(Number(e.target.value))} />
            </div>
            <div>
              <label className="text-xs text-stone-500">{t('admin.trade_price_note', lang)}</label>
              <input type="number" className="input mt-1" min={0.01} step={0.01} value={price} onChange={(e) => setPrice(Number(e.target.value))} onBlur={(e) => e.target.value && setPrice(round2(Number(e.target.value)))} />
            </div>
          </>
        )}
        <div className={isStock ? '' : 'sm:col-span-2'}>
          <label className="text-xs text-stone-500">{isStock ? t('admin.trade_settlement', lang) : t('admin.trade_transfer', lang)}</label>
          <input type="number" className="input mt-1" min={0.01} step={0.01} value={total} onChange={(e) => setTotal(Number(e.target.value))} onBlur={(e) => e.target.value && setTotal(round2(Number(e.target.value)))} />
        </div>
      </div>
      <button type="button" className="btn-primary w-full mt-4" disabled={append.isPending || total <= 0} onClick={() => append.mutate()}>
        {t('admin.trade_submit', lang)}
      </button>
    </div>
  )
}
