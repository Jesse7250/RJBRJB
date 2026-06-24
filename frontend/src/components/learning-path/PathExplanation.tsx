/**
 * 需求：学习路径可解释性前端组件（C7）。
 * 功能：
 *   - 按顺序展示推荐学习路径的每个知识点；
 *   - 鼠标悬停/点击时显示该步骤的推荐理由（前置依赖、掌握度、易错点等）；
 *   - 支持点击步骤触发资源生成。
 *
 * TODO:
 * - [已完成] 路径节点与推荐理由 Tooltip
 * - [已完成] 点击节点生成资源
 * - [待完成] 与知识图谱可视化联动高亮
 */
import { ArrowRight, MapPin, Sparkles } from 'lucide-react'

import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Tooltip, TooltipContent, TooltipProvider, TooltipTrigger } from '@/components/ui/tooltip'
import { cn } from '@/lib/utils'

interface Props {
  path: string[]
  explanations?: string[]
  estimatedMinutes?: number
  onGenerate?: (concept: string) => void
  className?: string
}

export function PathExplanation({ path, explanations, estimatedMinutes, onGenerate, className }: Props) {
  if (!path || path.length === 0) return null

  return (
    <TooltipProvider delayDuration={100}>
      <div className={cn('rounded-xl border border-indigo-100 bg-indigo-50/60 p-3', className)}>
        <div className="mb-2 flex items-center gap-2 text-xs font-bold text-indigo-700">
          <MapPin className="h-3.5 w-3.5" />
          推荐学习路径
        </div>
        <div className="flex flex-wrap items-center gap-2">
          {path.map((step, i) => {
            const reason = explanations?.[i]
            const isLast = i === path.length - 1
            return (
              <div key={`${step}-${i}`} className="flex items-center gap-2">
                <Tooltip>
                  <TooltipTrigger asChild>
                    <Badge
                      variant="secondary"
                      className={cn(
                        'cursor-help border-0 bg-white text-xs font-semibold text-slate-700 shadow-sm transition-all hover:-translate-y-0.5 hover:shadow-md',
                        isLast && 'bg-gradient-to-r from-indigo-500 to-violet-600 text-white'
                      )}
                    >
                      {step}
                    </Badge>
                  </TooltipTrigger>
                  <TooltipContent side="top" className="max-w-xs">
                    <div className="space-y-1">
                      <p className="font-bold">{step}</p>
                      {reason ? (
                        <p className="text-slate-600">{reason}</p>
                      ) : (
                        <p className="text-slate-500">推荐按此顺序学习，以建立完整的前置知识。</p>
                      )}
                      {onGenerate && (
                        <Button
                          size="sm"
                          className="mt-2 h-7 gap-1 rounded-lg bg-gradient-to-r from-indigo-600 to-violet-600 text-[10px]"
                          onClick={() => onGenerate(step)}
                        >
                          <Sparkles className="h-3 w-3" />
                          生成资源
                        </Button>
                      )}
                    </div>
                  </TooltipContent>
                </Tooltip>
                {!isLast && <ArrowRight className="h-3 w-3 text-indigo-400" />}
              </div>
            )
          })}
        </div>
        {estimatedMinutes ? (
          <p className="mt-2 text-[10px] text-slate-500">预计学习时长：{estimatedMinutes} 分钟</p>
        ) : null}
      </div>
    </TooltipProvider>
  )
}
