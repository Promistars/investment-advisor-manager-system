import * as echarts from 'echarts'
import { useEffect, useRef } from 'react'

/** 原生 ECharts 挂载，避免 react-echarts-for-react 在 React 19 下 insertBefore 崩溃 */
export function EChartBox({ option, height = 360 }: { option: echarts.EChartsCoreOption; height?: number }) {
  const el = useRef<HTMLDivElement>(null)
  const chartRef = useRef<echarts.ECharts | null>(null)

  useEffect(() => {
    const node = el.current
    if (!node) return
    const chart = echarts.init(node)
    chartRef.current = chart
    const ro = new ResizeObserver(() => chart.resize())
    ro.observe(node)
    return () => {
      ro.disconnect()
      chart.dispose()
      chartRef.current = null
    }
  }, [])

  useEffect(() => {
    chartRef.current?.setOption(option, { notMerge: true, lazyUpdate: true })
    chartRef.current?.resize()
  }, [option])

  return <div ref={el} style={{ height, width: '100%' }} className="min-w-0" />
}
