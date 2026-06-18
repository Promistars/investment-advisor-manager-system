/** 旧版客户链接 ?user=&acc= 重定向到 /client/{user}/{account} */
export function clientLinkFromQuery(params: URLSearchParams): string | null {
  const user = params.get('user')
  const acc = params.get('acc')
  if (!user || !acc) return null

  const q = new URLSearchParams()
  const lang = params.get('lang')
  if (lang) q.set('lang', lang)

  const view = params.get('view')
  if (view) {
    const map: Record<string, string> = {
      month: 'monthly',
      quarter: 'quarterly',
      year: 'yearly',
      monthly: 'monthly',
      quarterly: 'quarterly',
      yearly: 'yearly',
      custom: 'custom',
    }
    q.set('view', map[view] || view)
  }

  const qs = q.toString()
  return `/client/${encodeURIComponent(user)}/${encodeURIComponent(acc)}${qs ? `?${qs}` : ''}`
}
