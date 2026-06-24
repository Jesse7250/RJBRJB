/**
 * 需求：掌握度热力图前端组件（C6）。
 * 功能：
 *   - 调用 `/api/evaluation/heatmap` 获取 BKT 掌握概率；
 *   - 按掌握度区间着色展示各知识点；
 *   - 展示汇总统计与图例。
 *
 * TODO:
 * - [已完成] 基础网格热力图
 * - [已完成] 汇总统计与图例
 * - [待完成] 点击知识点下钻到 BKT 详情
 * - [待完成] 趋势曲线
 */
import { useEffect, useState } from 'react'
import { motion } from 'framer-motion'
import { Activity, Brain } from 'lucide-react'

import { GlassCard } from '@/components/ui/glass-card'
import { Skeleton } from '@/components/ui/skeleton'
import { EmptyState } from '@/components/ui/empty-state'
import { IconBox } from '@/components/ui/icon-box'
import { evaluationApi } from '@/services/api'
import { cn } from '@/lib/utils'

interface HeatmapItem {
  concept: string
  mastery_probability: number
  observation_count: number
  is_mastered: boolean
}

interface HeatmapSummary {
  total_concepts: number
  mastered: number
  average_probability: number
}

interface Props {
  sessionId?: string
}

function SummaryBox({ label, value }: { label: string; value: string | number }) {
  return (
    <div className="rounded-xl border border-white/60 bg-white/60 p-3 text-center shadow-sm backdrop-blur-sm">
      <div className="text-lg font-bold text-slate-900">{value}</div>
      <div className="text-[10px] font-medium uppercase tracking-wider text-slate-500">{label}</div>
    </div>
  )
}

function getColorClass(probability: number) {
  if (probability >= 0.85) return 'bg-emerald-500 text-white shadow-emerald-500/20'
  if (probability >= 0.6) return 'bg-amber-400 text-slate-900 shadow-amber-400/20'
  if (probability >= 0.3) return 'bg-orange-400 text-white shadow-orange-400/20'
  return 'bg-rose-500 text-white shadow-rose-500/20'
}

export function MasteryHeatmap({ sessionId }: Props) {
  const [data, setData] = useState<HeatmapItem[]>([])
  const [summary, setSummary] = useState<HeatmapSummary | null>(null)
  const [loading, setLoading] = useState(false)

  useEffect(() => {
    if (!sessionId) return
    setLoading(true)
    evaluationApi
      .getHeatmap(sessionId)
      .then((res) => {
        setData(res.data.data || [])
        setSummary(res.data.summary || null)
      })
      .catch(() => {
        setData([])
        setSummary(null)
      })
      .finally(() => setLoading(false))
  }, [sessionId])

  return (
    <GlassCard className="flex h-[calc(100vh-12rem)] min-h-[520px] flex-col overflow-hidden" hover={false}>
      <div className="flex items-center justify-between border-b border-slate-100 bg-gradient-to-r from-indigo-50/50 to-violet-50/50 px-5 py-4">
        <div className="flex items-center gap-3">
          <IconBox icon={Activity} variant="indigo" size="sm" />
          <div>
            <h3 className="text-base font-bold text-slate-900">掌握度热力图</h3>
            <p className="text-xs text-slate-500">基于 BKT 的实时掌握概率</p>
          </div>
        </div>
      </div>

      <div className="flex-1 overflow-y-auto p-5">
        {loading ? (
          <div className="space-y-3">
            <Skeleton className="h-20 w-full" />
            <Skeleton className="h-40 w-full" />
          </div>
        ) : (
          <>
            {summary && (
              <div className="mb-5 grid grid-cols-3 gap-3">
                <SummaryBox label="知识点" value={summary.total_concepts} />
                <SummaryBox label="已掌握" value={summary.mastered} />
                <SummaryBox
                  label="平均掌握度"
                  value={`${(summary.average_probability * 100).toFixed(0)}%`}
                />
              </div>
            )}

            {data.length > 0 ? (
              <div className="grid grid-cols-2 gap-3 sm:grid-cols-3 lg:grid-cols-4">
                {data.map((item) => (
                  <motion.div
                    key={item.concept}
                    whileHover={{ scale: 1.03 }}
                    className={cn(
                      'rounded-2xl p-4 text-center shadow-lg backdrop-blur-sm transition-transform',
                      getColorClass(item.mastery_probability)
                    )}
                  >
                    <div className="text-xs font-semibold opacity-95">{item.concept}</div>
                    <div className="mt-1 text-2xl font-extrabold">
                      {(item.mastery_probability * 100).toFixed(0)}%
                    </div>
                    <div className="text-[10px] opacity-90">{item.observation_count} 次练习</div>
                  </motion.div>
                ))}
              </div>
            ) : (
              <EmptyState
                icon={Brain}
                title="暂无掌握度数据"
                description="完成一些练习或代码判题后，热力图会自动更新。"
                variant="indigo"
              />
            )}

            <div className="mt-6 flex flex-wrap items-center gap-3 text-[10px] font-medium text-slate-500">
              <span className="flex items-center gap-1.5">
                <span className="h-3 w-3 rounded-full bg-emerald-500" /> 已掌握
              </span>
              <span className="flex items-center gap-1.5">
                <span className="h-3 w-3 rounded-full bg-amber-400" /> 需巩固
              </span>
              <span className="flex items-center gap-1.5">
                <span className="h-3 w-3 rounded-full bg-orange-400" /> 薄弱
              </span>
              <span className="flex items-center gap-1.5">
                <span className="h-3 w-3 rounded-full bg-rose-500" /> 待学习
              </span>
            </div>
          </>
        )}
      </div>
    </GlassCard>
  )
}
