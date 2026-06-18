import { useEffect, useMemo, useState } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { useAuth } from '../context/AuthContext'
import { api } from '../lib/api'
import { t, type Lang } from '../lib/i18n'

export function CommentaryEditor({
  account,
  reportPeriods,
}: {
  account: string
  reportPeriods: Record<string, string>
}) {
  const { prefs } = useAuth()
  const lang = prefs.lang
  const qc = useQueryClient()
  const options = useMemo(() => Object.values(reportPeriods), [reportPeriods])
  const [rep, setRep] = useState(options[0] || '')
  const [html, setHtml] = useState('')
  const [confirmDel, setConfirmDel] = useState<string | null>(null)

  const { data: loaded } = useQuery({
    queryKey: ['commentary', account, rep],
    queryFn: () => api.getCommentary(account, rep),
    enabled: !!rep,
  })

  const { data: archive = {} } = useQuery({
    queryKey: ['commentaries', account],
    queryFn: () => api.listCommentaries(account),
  })

  useEffect(() => {
    setHtml(loaded?.html || '')
  }, [loaded?.html, rep])

  useEffect(() => {
    if (!rep && options[0]) setRep(options[0])
  }, [options, rep])

  const save = useMutation({
    mutationFn: () => api.saveCommentary(account, rep, html),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['commentaries', account] })
      qc.invalidateQueries({ queryKey: ['admin', account] })
    },
  })

  const del = useMutation({
    mutationFn: (name: string) => api.deleteCommentary(account, name),
    onSuccess: () => {
      setConfirmDel(null)
      qc.invalidateQueries({ queryKey: ['commentaries', account] })
    },
  })

  return (
    <div className="card p-5 space-y-4">
      <h3 className="font-bold text-brand-700">{t('commentary.manage', lang)}</h3>
      <select className="input" value={rep} onChange={(e) => setRep(e.target.value)}>
        {options.map((o) => (
          <option key={o}>{o}</option>
        ))}
      </select>
      <div className="grid lg:grid-cols-2 gap-4">
        <div>
          <p className="text-xs text-stone-500 mb-1">{t('commentary.html_edit', lang)}</p>
          <textarea
            className="input min-h-[220px] font-mono text-xs leading-relaxed"
            value={html}
            onChange={(e) => setHtml(e.target.value)}
            placeholder={t('commentary.placeholder', lang)}
          />
        </div>
        <div>
          <p className="text-xs text-stone-500 mb-1">{t('commentary.preview', lang)}</p>
          <div
            className="border border-stone-100 rounded-xl p-4 min-h-[220px] prose prose-sm max-w-none"
            dangerouslySetInnerHTML={{ __html: html || `<p class="text-stone-400">${t('commentary.preview_empty', lang)}</p>` }}
          />
        </div>
      </div>
      <details className="text-xs text-stone-500">
        <summary>{t('commentary.advanced', lang)}</summary>
        <p className="mt-2">链接: [文字](http://example.com)</p>
        <p>字体: [文字](font:楷体) — 支持楷体/宋体/黑体/微软雅黑/Times</p>
      </details>
      <button type="button" className="btn-primary" onClick={() => save.mutate()} disabled={save.isPending || !rep}>
        {t('commentary.save', lang)}
      </button>
      {Object.keys(archive).length > 0 && (
        <div className="border-t border-stone-100 pt-4 space-y-2">
          <h4 className="font-medium text-sm">{t('commentary.archive', lang)}</h4>
          {Object.entries(archive).map(([name, txt]) => (
            <details key={name} className="border border-stone-100 rounded-lg p-2">
              <summary className="cursor-pointer text-sm">{account} — {name}</summary>
              <div className="prose prose-sm mt-2 max-w-none" dangerouslySetInnerHTML={{ __html: txt }} />
              {confirmDel === name ? (
                <div className="flex gap-2 mt-2">
                  <button type="button" className="btn-primary text-xs" onClick={() => del.mutate(name)}>
                    {t('commentary.confirm_del', lang)}
                  </button>
                  <button type="button" className="btn-secondary text-xs" onClick={() => setConfirmDel(null)}>
                    {t('common.cancel', lang)}
                  </button>
                </div>
              ) : (
                <button type="button" className="text-xs text-red-600 mt-2" onClick={() => setConfirmDel(name)}>
                  {t('commentary.del', lang)}
                </button>
              )}
            </details>
          ))}
        </div>
      )}
    </div>
  )
}

export function SharePanel({ clientUrl, lang = 'zh' }: { clientUrl: string; lang?: Lang }) {
  const [copied, setCopied] = useState(false)
  const copy = (url: string) => {
    navigator.clipboard.writeText(url)
    setCopied(true)
    setTimeout(() => setCopied(false), 2000)
  }
  return (
    <div className="card p-4 space-y-3">
      <h3 className="font-semibold">{t('share.client_links', lang)}</h3>
      <p className="text-xs text-stone-500">{t('share.hint_client', lang)}</p>
      <div>
        <div className="text-xs text-stone-500 mb-1">{t('share.link', lang)}</div>
        <code className="block text-xs bg-stone-50 p-2 rounded-lg break-all">{clientUrl}</code>
        <button type="button" className="btn-secondary mt-2 text-xs" onClick={() => copy(clientUrl)}>
          {copied ? t('share.copied', lang) : t('share.copy', lang)}
        </button>
      </div>
    </div>
  )
}
