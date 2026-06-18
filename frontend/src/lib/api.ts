export interface AdminBundle {
  ok: boolean
  message?: string
  benchmark: string
  account: string
  view: string
  available_views: string[]
  period_start: string
  period_end: string
  max_selectable_date?: string
  account_start?: string
  kpi: {
    period_return: number
    benchmark_level: number
    benchmark_return: number
    alpha: number
    total_asset: number
    max_drawdown: number
    sharpe_ratio: number
    period_net_inflow: number
    engine_principal: number
    ledger_in: number
    ledger_out: number
  }
  charts: Array<{
    日期: string
    账户累计收益率: number
    大盘累计收益率: number
    总持仓市值: number
    累计净本金: number
  }>
  commentary: { period: string; html: string }
  trades?: TradeRow[]
  admin: AdminMeta
}

export interface AdminMeta {
  snap_date: string
  cash: number
  fees: number
  engine_principal: number
  ledger_net: number
  ledger_in: number
  ledger_out: number
  principal_mismatch: boolean
  account_start: string
  global_min_date: string
  global_max_date: string
  stock_names: string[]
  last_trade_type: string
  holdings: Array<{ name: string; value: number; shares: number; pct: number }>
  timeline: {
    series: Array<{ 日期: string; 总持仓市值: number; 累计净本金: number }>
    markers: Array<{ date: string; type: string; label: string; color: string; y: number; amount: number }>
  }
  statement: Array<Record<string, unknown>>
  report_periods: Record<string, string>
  invalid_trade_indices?: number[]
  total_asset: number
  unrealized_pnl: number
  return_pct: number
  position_count: number
  cash_pct: number
  stock_pct: number
  nav: number
  trade_count: number
}

export interface TradeRow {
  日期: string
  操作类型: string
  标的: string
  '数量(股)': number | null
  '成交单价(¥)': number | null
  '实际结算总金额(¥)': number | null
}

export interface BillingState {
  last_watermark_date: string
  adjusted_watermark: number
  current_asset: number
  period_profit: number
  target_mode: string
  target_pct: number
  target_asset: number
  fee_ratio: number
  reached: boolean
  fee_amount: number
  extra_profit: number
  agreed_profit: number
  billing_history: Array<{ date: string; type: string; watermark: number; fee_amount: number }>
}

export interface AccountSummary {
  name: string
  last_accessed?: string | null
  principal: number
  pnl: number
  pnl_pct: number
  total_asset: number
  as_of_date: string
  fees_collected?: number
}

export interface UserPrefs {
  lang: 'zh' | 'en'
  pnl_colors: 'cn' | 'western'
  date_format: 'iso' | 'cn' | 'us'
  compact_ui: boolean
  show_emoji: boolean
  default_view: 'month' | 'quarter' | 'year'
}

/** Avoid `new URL(relative, '/IAMS/')` — throws in Node and some mobile WebViews. */
function resolveApiBase(): string {
  const root = import.meta.env.BASE_URL || '/IAMS/'
  const normalized = root.endsWith('/') ? root : `${root}/`
  return `${normalized}api`.replace(/\/+$/, '')
}

const BASE = resolveApiBase()

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${BASE}${path}`, {
    credentials: 'include',
    headers: { 'Content-Type': 'application/json', ...(init?.headers || {}) },
    ...init,
  })
  if (!res.ok) {
    let detail = res.statusText
    try {
      const body = await res.json()
      detail = body.detail || body.message || detail
    } catch {
      /* ignore */
    }
    throw new Error(String(detail))
  }
  if (res.status === 204) return undefined as T
  return res.json()
}

export const api = {
  health: () => request<{ status: string; version: string }>('/health'),
  login: (username: string, password: string) =>
    request<{ username: string }>('/auth/login', { method: 'POST', body: JSON.stringify({ username, password }) }),
  register: (username: string, password: string) =>
    request('/auth/register', { method: 'POST', body: JSON.stringify({ username, password }) }),
  logout: () => request('/auth/logout', { method: 'POST' }),
  me: () => request<{ username: string }>('/auth/me'),
  changePassword: (old_password: string, new_password: string) =>
    request('/auth/password', { method: 'PUT', body: JSON.stringify({ old_password, new_password }) }),
  accounts: () => request<AccountSummary[]>('/accounts'),
  feeTotal: () => request<{ total_fees: number; account_count: number }>('/accounts/fee-total'),
  createAccount: (name: string) => request('/accounts', { method: 'POST', body: JSON.stringify({ name }) }),
  deleteAccount: (name: string) => request(`/accounts/${encodeURIComponent(name)}`, { method: 'DELETE' }),
  touchAccount: (name: string) => request(`/accounts/${encodeURIComponent(name)}/touch`, { method: 'POST' }),
  getStartDate: (name: string) =>
    request<{ start_date: string; global_min_date: string; global_max_date: string }>(
      `/accounts/${encodeURIComponent(name)}/start-date`,
    ),
  setStartDate: (name: string, start_date: string) =>
    request(`/accounts/${encodeURIComponent(name)}/start-date`, {
      method: 'PUT',
      body: JSON.stringify({ start_date }),
    }),
  getTrades: (name: string) => request<{ trades: TradeRow[] }>(`/accounts/${encodeURIComponent(name)}/trades`),
  saveTrades: (name: string, trades: TradeRow[]) =>
    request(`/accounts/${encodeURIComponent(name)}/trades`, {
      method: 'PUT',
      body: JSON.stringify({ trades }),
    }),
  adminBundle: (name: string, view: string, custom?: { start?: string; end?: string }) => {
    const q = new URLSearchParams({ view })
    if (custom?.start) q.set('custom_start', custom.start)
    if (custom?.end) q.set('custom_end', custom.end)
    return request<AdminBundle>(`/accounts/${encodeURIComponent(name)}/admin?${q}`)
  },
  appendTrade: (name: string, row: Record<string, unknown>) =>
    request(`/accounts/${encodeURIComponent(name)}/admin/trades/append`, {
      method: 'POST',
      body: JSON.stringify(row),
    }),
  removeTradeIndices: (name: string, indices: number[]) =>
    request(`/accounts/${encodeURIComponent(name)}/admin/trades/remove-indices`, {
      method: 'POST',
      body: JSON.stringify({ indices }),
    }),
  suggestedPrice: (name: string, asset: string, on_date: string) =>
    request<{ price: number }>(
      `/accounts/${encodeURIComponent(name)}/admin/suggested-price?asset=${encodeURIComponent(asset)}&on_date=${on_date}`,
    ),
  billingPreview: (name: string, body: Record<string, unknown>) =>
    request<BillingState>(`/accounts/${encodeURIComponent(name)}/admin/billing/preview`, {
      method: 'POST',
      body: JSON.stringify(body),
    }),
  billingHistoricalPreview: (name: string, body: Record<string, unknown>) =>
    request<Record<string, unknown>>(`/accounts/${encodeURIComponent(name)}/admin/billing/historical-preview`, {
      method: 'POST',
      body: JSON.stringify(body),
    }),
  billingExecute: (name: string, body: Record<string, unknown>) =>
    request(`/accounts/${encodeURIComponent(name)}/admin/billing/execute`, {
      method: 'POST',
      body: JSON.stringify(body),
    }),
  dashboard: (name: string, view: string, custom?: { start?: string; end?: string }) => {
    const q = new URLSearchParams({ view })
    if (custom?.start) q.set('custom_start', custom.start)
    if (custom?.end) q.set('custom_end', custom.end)
    return request<AdminBundle>(`/accounts/${encodeURIComponent(name)}/dashboard?${q}`)
  },
  clientDashboard: (user: string, acc: string, view: string, custom?: { start?: string; end?: string }) => {
    const q = new URLSearchParams({ view })
    if (custom?.start) q.set('custom_start', custom.start)
    if (custom?.end) q.set('custom_end', custom.end)
    return request<AdminBundle>(
      `/public/client/${encodeURIComponent(user)}/${encodeURIComponent(acc)}/dashboard?${q}`,
    )
  },
  prefs: () => request<UserPrefs>('/prefs'),
  savePrefs: (prefs: Partial<UserPrefs>) =>
    request<UserPrefs>('/prefs', { method: 'PUT', body: JSON.stringify({ prefs }) }),
  resetPrefs: () => request<UserPrefs>('/prefs/reset', { method: 'POST' }),
  stocks: () => request<{ stocks: string[]; eastmoney_kline: boolean }>('/stocks'),
  ingestStock: (name: string, force = false) =>
    request<{ message: string }>('/stocks/ingest', { method: 'POST', body: JSON.stringify({ name, force }) }),
  listCommentaries: (acc: string) => request<Record<string, string>>(`/accounts/${encodeURIComponent(acc)}/commentaries`),
  getCommentary: (acc: string, report: string) =>
    request<{ html: string }>(`/accounts/${encodeURIComponent(acc)}/commentaries/${encodeURIComponent(report)}`),
  saveCommentary: (acc: string, report: string, html: string) =>
    request(`/accounts/${encodeURIComponent(acc)}/commentaries/${encodeURIComponent(report)}`, {
      method: 'PUT',
      body: JSON.stringify({ report_name: report, html }),
    }),
  deleteCommentary: (acc: string, report: string) =>
    request(`/accounts/${encodeURIComponent(acc)}/commentaries/${encodeURIComponent(report)}`, { method: 'DELETE' }),
  refreshPnl: () => request('/maintenance/refresh-pnl', { method: 'POST' }),
}
