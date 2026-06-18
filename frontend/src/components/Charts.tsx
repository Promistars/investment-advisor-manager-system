import type { EChartsCoreOption } from 'echarts'
import type { UserPrefs } from '../lib/api'
import { fmtMoney, fmtPct } from '../lib/format'
import { t } from '../lib/i18n'
import { EChartBox } from './EChartBox'

interface Point {
  日期: string
  账户累计收益率: number
  大盘累计收益率: number
  总持仓市值: number
  累计净本金: number
}

export function ReturnChart({ data, prefs }: { data: Point[]; prefs: UserPrefs }) {
  const lang = prefs.lang
  const dates = data.map((d) => d.日期)
  const option: EChartsCoreOption = {
    backgroundColor: 'transparent',
    grid: { left: 48, right: 16, top: 40, bottom: 32 },
    tooltip: {
      trigger: 'axis',
      valueFormatter: (value: number) => fmtPct(Number(value)),
    },
    legend: {
      data: [t('chart.portfolio', lang), t('chart.benchmark', lang)],
      top: 0,
    },
    xAxis: { type: 'category', data: dates, boundaryGap: false },
    yAxis: {
      type: 'value',
      axisLabel: { formatter: '{value}%' },
      splitLine: { lineStyle: { color: '#f5f5f4' } },
    },
    series: [
      {
        name: t('chart.benchmark', lang),
        type: 'line',
        data: data.map((d) => d.大盘累计收益率),
        smooth: true,
        lineStyle: { color: '#3b82f6', type: 'dotted' },
        areaStyle: { color: 'rgba(59,130,246,0.06)' },
        symbol: 'none',
      },
      {
        name: t('chart.portfolio', lang),
        type: 'line',
        data: data.map((d) => d.账户累计收益率),
        smooth: true,
        lineStyle: { color: '#dc2626', width: 2.5 },
        areaStyle: { color: 'rgba(220,38,38,0.08)' },
        symbol: 'none',
      },
      {
        name: t('chart.breakeven', lang),
        type: 'line',
        data: dates.map(() => 0),
        lineStyle: { color: '#c9a227', type: 'dashed' },
        symbol: 'none',
        tooltip: { show: false },
      },
    ],
  }
  return <EChartBox option={option} height={360} />
}

export function AssetChart({ data, prefs }: { data: Point[]; prefs: UserPrefs }) {
  const lang = prefs.lang
  const dates = data.map((d) => d.日期)
  const option: EChartsCoreOption = {
    backgroundColor: 'transparent',
    grid: { left: 64, right: 16, top: 40, bottom: 32 },
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
      splitLine: { lineStyle: { color: '#f5f5f4' } },
    },
    series: [
      {
        name: t('chart.total_assets', lang),
        type: 'line',
        data: data.map((d) => d.总持仓市值),
        smooth: true,
        lineStyle: { color: '#dc2626', width: 2.5 },
        areaStyle: { color: 'rgba(220,38,38,0.08)' },
        symbol: 'none',
      },
      {
        name: t('chart.net_principal', lang),
        type: 'line',
        data: data.map((d) => d.累计净本金),
        smooth: true,
        lineStyle: { color: '#c9a227', type: 'dashed' },
        symbol: 'none',
      },
    ],
  }
  return <EChartBox option={option} height={360} />
}

