import { useEffect, useRef, useState } from 'react'
import * as echarts from 'echarts'
import { Share2 } from 'lucide-react'

import { GlassCard } from '@/components/ui/glass-card'
import { IconBox } from '@/components/ui/icon-box'
import { Skeleton } from '@/components/ui/skeleton'
import { graphApi, type GraphData } from '@/services/api'

const MODULE_COLORS: Record<string, string> = {
  基础语法: '#6366f1',
  数据类型: '#10b981',
  控制流: '#f59e0b',
  函数: '#ec4899',
  面向对象: '#06b6d4',
  标准库: '#8b5cf6',
}

const FALLBACK_PALETTE = ['#6366f1', '#10b981', '#f59e0b', '#ec4899', '#06b6d4', '#8b5cf6']

export function KnowledgeGraph() {
  const [graphData, setGraphData] = useState<GraphData | null>(null)
  const [loading, setLoading] = useState(true)
  const chartRef = useRef<HTMLDivElement>(null)
  const chartInstanceRef = useRef<echarts.ECharts | null>(null)

  useEffect(() => {
    graphApi.getGraph().then((res) => {
      setGraphData(res.data)
      setLoading(false)
    })
  }, [])

  useEffect(() => {
    if (!graphData || !chartRef.current) return

    const modules = Array.from(new Set(graphData.nodes.map((n) => n.module)))
    const categories = modules.map((name, index) => ({
      name,
      itemStyle: {
        color: MODULE_COLORS[name] || FALLBACK_PALETTE[index % FALLBACK_PALETTE.length],
      },
    }))

    const categoryIndex = (module: string) => modules.indexOf(module)

    const nodes = graphData.nodes.map((n) => ({
      id: n.id,
      name: n.name,
      value: n.difficulty,
      category: categoryIndex(n.module),
      symbolSize: 24 + n.difficulty * 5,
      label: { show: true, formatter: '{b}', fontSize: 12, fontWeight: 600 },
      itemStyle: {
        color: MODULE_COLORS[n.module] || FALLBACK_PALETTE[categoryIndex(n.module) % FALLBACK_PALETTE.length],
        borderColor: '#fff',
        borderWidth: 2,
        shadowBlur: 10,
        shadowColor: 'rgba(0,0,0,0.12)',
      },
    }))

    const links = graphData.edges.map((e) => ({
      source: e.source,
      target: e.target,
      value: e.strength,
      lineStyle: { width: 1 + e.strength * 2, opacity: 0.5 },
    }))

    const chart = echarts.init(chartRef.current, undefined, { renderer: 'canvas' })
    chartInstanceRef.current = chart

    chart.setOption({
      backgroundColor: 'transparent',
      tooltip: {
        trigger: 'item',
        backgroundColor: 'rgba(255,255,255,0.96)',
        borderColor: '#e2e8f0',
        borderWidth: 1,
        padding: [10, 14],
        textStyle: { color: '#1e293b' },
        formatter: (params: any) => {
          if (params.dataType === 'edge') return `${params.data.source} → ${params.data.target}`
          const data = params.data as any
          return `<div class="font-sans">
            <div class="font-bold text-slate-900">${data.name}</div>
            <div class="text-xs text-slate-500">模块：${categories[data.category]?.name}</div>
            <div class="text-xs text-slate-500">难度：${data.value}/5</div>
          </div>`
        },
      },
      legend: {
        top: 0,
        left: 'center',
        itemGap: 18,
        textStyle: { color: '#64748b', fontSize: 12, fontWeight: 500 },
        data: categories.map((c) => c.name),
      },
      animationDuration: 1600,
      animationEasingUpdate: 'quinticInOut',
      series: [
        {
          name: 'Python 知识图谱',
          type: 'graph',
          layout: 'force',
          data: nodes,
          links,
          categories,
          roam: true,
          draggable: true,
          label: { show: true, position: 'bottom' },
          force: {
            repulsion: 480,
            edgeLength: [80, 150],
            gravity: 0.08,
          },
          emphasis: {
            focus: 'adjacency',
            lineStyle: { width: 4, opacity: 1 },
            itemStyle: { shadowBlur: 18, shadowColor: 'rgba(0,0,0,0.2)' },
          },
          lineStyle: {
            color: 'source',
            curveness: 0.05,
          },
        },
      ],
    })

    const handleResize = () => chart.resize()
    window.addEventListener('resize', handleResize)

    return () => {
      window.removeEventListener('resize', handleResize)
      chart.dispose()
      chartInstanceRef.current = null
    }
  }, [graphData])

  return (
    <GlassCard className="overflow-hidden" hover={false}>
      <div className="flex items-center justify-between border-b border-slate-100 bg-gradient-to-r from-violet-50/50 to-indigo-50/50 px-5 py-4">
        <div className="flex items-center gap-3">
          <IconBox icon={Share2} variant="violet" size="sm" />
          <div>
            <h3 className="text-base font-bold text-slate-900">Python 知识图谱</h3>
            <p className="text-xs text-slate-500">力导向图 · 按模块着色</p>
          </div>
        </div>
      </div>
      <div className="p-5">
        {loading ? (
          <div className="flex h-[500px] flex-col items-center justify-center gap-3 text-slate-500">
            <Skeleton className="h-10 w-10 rounded-full" />
            <span className="text-sm">正在加载知识图谱...</span>
          </div>
        ) : (
          <div
            ref={chartRef}
            className="h-[500px] w-full rounded-2xl border border-slate-100 bg-slate-50/50"
          />
        )}
      </div>
    </GlassCard>
  )
}
