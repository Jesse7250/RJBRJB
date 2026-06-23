import { useEffect, useRef, useState } from 'react'

import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { graphApi, type GraphData } from '@/services/api'

/**
 * TODO:
 * - [待完成] 使用 ECharts 或 D3 替换 Canvas 实现更美观的力导向图
 * - [待完成] 高亮已掌握、当前目标、未学节点
 * - [待完成] 点击节点显示详情并触发学习
 * - [待完成] 显示个人学习路径
 * - [待完成] 按模块着色与图例
 */

export function KnowledgeGraph() {
  const [graphData, setGraphData] = useState<GraphData | null>(null)
  const [loading, setLoading] = useState(true)
  const containerRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    graphApi.getGraph().then((res) => {
      setGraphData(res.data)
      setLoading(false)
    })
  }, [])

  // 简单力导向图渲染
  useEffect(() => {
    if (!graphData || !containerRef.current) return

    const canvas = document.createElement('canvas')
    const container = containerRef.current
    container.innerHTML = ''
    container.appendChild(canvas)

    const width = container.clientWidth
    const height = 500
    canvas.width = width
    canvas.height = height

    const ctx = canvas.getContext('2d')
    if (!ctx) return

    const nodes = graphData.nodes.map((n) => ({
      ...n,
      x: Math.random() * width,
      y: Math.random() * height,
      vx: 0,
      vy: 0,
    }))

    const edges = graphData.edges

    function animate() {
      if (!ctx) return
      ctx.clearRect(0, 0, width, height)

      // 简单的力导向模拟
      for (let i = 0; i < nodes.length; i++) {
        for (let j = i + 1; j < nodes.length; j++) {
          const dx = nodes[j].x - nodes[i].x
          const dy = nodes[j].y - nodes[i].y
          const dist = Math.sqrt(dx * dx + dy * dy) || 1
          const force = 500 / (dist * dist)
          const fx = (dx / dist) * force
          const fy = (dy / dist) * force
          nodes[i].vx -= fx
          nodes[i].vy -= fy
          nodes[j].vx += fx
          nodes[j].vy += fy
        }
      }

      for (const edge of edges) {
        const source = nodes.find((n) => n.id === edge.source)
        const target = nodes.find((n) => n.id === edge.target)
        if (source && target) {
          const dx = target.x - source.x
          const dy = target.y - source.y
          const dist = Math.sqrt(dx * dx + dy * dy) || 1
          const force = (dist - 100) * 0.01
          const fx = (dx / dist) * force
          const fy = (dy / dist) * force
          source.vx += fx
          source.vy += fy
          target.vx -= fx
          target.vy -= fy

          ctx.beginPath()
          ctx.moveTo(source.x, source.y)
          ctx.lineTo(target.x, target.y)
          ctx.strokeStyle = 'rgba(148, 163, 184, 0.5)'
          ctx.lineWidth = 1
          ctx.stroke()
        }
      }

      for (const node of nodes) {
        node.vx *= 0.8
        node.vy *= 0.8
        node.x += node.vx
        node.y += node.vy

        // 边界约束
        node.x = Math.max(30, Math.min(width - 30, node.x))
        node.y = Math.max(30, Math.min(height - 30, node.y))

        ctx.beginPath()
        ctx.arc(node.x, node.y, 10 + node.difficulty * 2, 0, Math.PI * 2)
        ctx.fillStyle = `hsl(${210 + node.difficulty * 20}, 70%, 60%)`
        ctx.fill()

        ctx.fillStyle = '#334155'
        ctx.font = '12px sans-serif'
        ctx.textAlign = 'center'
        ctx.fillText(node.name, node.x, node.y + 30)
      }

      requestAnimationFrame(animate)
    }

    animate()
  }, [graphData])

  return (
    <Card>
      <CardHeader className="pb-3">
        <CardTitle className="text-lg">Python 知识图谱</CardTitle>
      </CardHeader>
      <CardContent>
        {loading ? (
          <div className="h-[500px] flex items-center justify-center text-muted-foreground">
            加载中...
          </div>
        ) : (
          <div ref={containerRef} className="h-[500px] w-full rounded-lg bg-slate-50 dark:bg-slate-900" />
        )}
      </CardContent>
    </Card>
  )
}
