import type { EChartsCoreOption } from 'echarts'
import { useAuth } from '../context/AuthContext'
import type { AdminMeta } from '../lib/api'
import { fmtMoney } from '../lib/format'
import { t } from '../lib/i18n'
import { EChartBox } from './EChartBox'

const MARKER_LETTER: Record<string, string> = {
  买入股票: 'B',
  卖出股票: 'S',
  转入本金: 'D',
  提取现金: 'W',
  '提取管理费(内扣)': 'F',
  '结账重置(外付)': 'F',
}

type PlacedMarker = {
  m: AdminMeta['timeline']['markers'][number]
  idx: number
  anchorY: number
  labelY: number
}

function layoutMarkers(timeline: AdminMeta['timeline'], dates: string[], lift: number, yMin: number): PlacedMarker[] {
  const byDate = new Map<string, AdminMeta['timeline']['markers']>()
  for (const m of timeline.markers) {
    const list = byDate.get(m.date) ?? []
    list.push(m)
    byDate.set(m.date, list)
  }

  const placed: PlacedMarker[] = []
  for (const [date, markers] of byDate) {
    const idx = dates.indexOf(date)
    if (idx < 0) continue
    markers.forEach((m, i) => {
      const above = i % 2 === 0
      const tier = Math.floor(i / 2)
      const liftAmount = lift * (1 + tier * 0.65)
      const labelY = above ? m.y + liftAmount : Math.max(m.y - liftAmount, yMin * 0.85)
      placed.push({ m, idx, anchorY: m.y, labelY })
    })
  }
  return placed
}

export function AdminTimelineChart({ timeline }: { timeline: AdminMeta['timeline'] }) {
  const { prefs } = useAuth()
  const lang = prefs.lang
  const dates = timeline.series.map((d) => d.日期)
  const assetValues = timeline.series.map((d) => d.总持仓市值)
  const yMax = Math.max(...assetValues, 1)
  const yMin = Math.min(...assetValues, 0)
  const ySpan = yMax - yMin || yMax * 0.1
  const lift = ySpan * 0.12

  const placed = layoutMarkers(timeline, dates, lift, yMin)
  const hasBelow = placed.some((p) => p.labelY < p.anchorY)
  const maxTier = Math.max(0, ...placed.map((p) => Math.abs(p.labelY - p.anchorY) / lift))

  const markLines = placed.map((p) => [
    { coord: [p.idx, p.anchorY], symbol: 'none' as const },
    { coord: [p.idx, p.labelY], symbol: 'none' as const },
  ])

  const scatterData = placed.map((p) => {
    const letter = MARKER_LETTER[p.m.type] ?? p.m.label.slice(0, 1)
    return {
      value: [p.idx, p.labelY],
      itemStyle: { color: p.m.color, borderColor: '#fff', borderWidth: 2 },
      label: {
        show: true,
        formatter: letter,
        color: '#fff',
        fontSize: 11,
        fontWeight: 'bold' as const,
      },
      symbolSize: 24,
      _tip: `${p.m.label} · ${p.m.date}<br/>${fmtMoney(p.m.amount, prefs)}`,
    }
  })

  const option: EChartsCoreOption = {
    grid: {
      left: 56,
      right: 16,
      top: 48 + maxTier * 8,
      bottom: hasBelow ? 48 + maxTier * 8 : 32,
    },
    tooltip: {
      trigger: 'axis',
      valueFormatter: (value: number) => fmtMoney(Number(value), prefs),
    },
    legend: { data: [t('chart.total_assets', lang), t('chart.net_principal', lang)], top: 0 },
    xAxis: { type: 'category', data: dates, boundaryGap: false },
    yAxis: {
      type: 'value',
      axisLabel: {
        formatter: (v: number) =>
          lang === 'zh' ? `¥${(v / 10000).toFixed(2)}万` : `¥${(v / 10000).toFixed(2)}w`,
      },
    },
    series: [
      {
        name: t('chart.total_assets', lang),
        type: 'line',
        data: assetValues,
        smooth: true,
        lineStyle: { color: '#3b82f6', width: 2 },
        symbol: 'none',
        markLine: markLines.length
          ? {
              silent: true,
              symbol: ['none', 'none'],
              lineStyle: { color: '#94a3b8', width: 1, type: 'solid' },
              data: markLines,
            }
          : undefined,
      },
      {
        name: t('chart.net_principal', lang),
        type: 'line',
        data: timeline.series.map((d) => d.累计净本金),
        smooth: true,
        lineStyle: { color: '#f59e0b', type: 'dashed' },
        symbol: 'none',
      },
      ...(scatterData.length
        ? [
            {
              name: t('admin.trade_type', lang),
              type: 'scatter' as const,
              data: scatterData,
              z: 10,
              tooltip: {
                trigger: 'item',
                formatter: (p: { data: { _tip?: string } }) => p.data._tip ?? '',
              },
            },
          ]
        : []),
    ],
  }
  return (
    <div>
      <h3 className="font-semibold text-brand-700 mb-2">{t('admin.timeline_title', lang)}</h3>
      <EChartBox option={option} height={420} />
    </div>
  )
}
