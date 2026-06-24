/**
 * 需求：苏格拉底提问链 UI（C8）。
 * 功能：
 *   - 展示当前引导问题与提示；
 *   - 提供「查看参考思路」与「继续引导」按钮；
 *   - 显示当前所处阶段（澄清/探查/验证/反例/收敛）。
 *
 * TODO:
 * - [已完成] 问题/提示/答案展示
 * - [已完成] 阶段标签与交互按钮
 * - [待完成] 与后端多轮 depth 联动，实现真正的 5 阶段递进
 */
import { useState } from 'react'
import { ChevronRight, Eye, HelpCircle, Lightbulb } from 'lucide-react'

import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { GlassCard } from '@/components/ui/glass-card'

const STAGE_NAMES: Record<string, string> = {
  clarification: '澄清问题',
  assumption_probe: '探查假设',
  evidence_check: '验证证据',
  counter_example: '反例思考',
  convergence: '收敛答案',
}

interface Props {
  question: string
  hint?: string
  answer?: string
  canProvideAnswer?: boolean
  stage?: string
  onNext?: () => void
  onReveal?: () => void
}

export function SocraticPanel({
  question,
  hint,
  answer,
  canProvideAnswer,
  stage,
  onNext,
  onReveal,
}: Props) {
  const [showAnswer, setShowAnswer] = useState(false)

  const handleReveal = () => {
    setShowAnswer(true)
    onReveal?.()
  }

  return (
    <GlassCard className="border-l-4 border-l-amber-400" hover={false}>
      <div className="mb-2 flex flex-wrap items-center gap-2 text-amber-700">
        <HelpCircle className="h-4 w-4" />
        <span className="font-bold">苏格拉底式辅导</span>
        {stage && (
          <Badge variant="secondary" className="text-[10px]">
            {STAGE_NAMES[stage] || stage}
          </Badge>
        )}
      </div>

      <p className="text-sm font-medium leading-relaxed text-slate-800">{question}</p>

      {hint && (
        <div className="mt-3 flex items-start gap-2 rounded-xl bg-amber-50/70 p-3 text-xs text-slate-600">
          <Lightbulb className="mt-0.5 h-3.5 w-3.5 shrink-0 text-amber-500" />
          <span>{hint}</span>
        </div>
      )}

      {answer && (showAnswer || canProvideAnswer) && (
        <div className="mt-3 rounded-xl border border-emerald-100 bg-emerald-50/70 p-3 text-xs text-emerald-800">
          <span className="font-bold">参考思路：</span>
          {answer}
        </div>
      )}

      <div className="mt-3 flex flex-wrap gap-2">
        {answer && !showAnswer && (
          <Button
            variant="outline"
            size="sm"
            className="h-8 gap-1 rounded-lg text-xs"
            onClick={handleReveal}
          >
            <Eye className="h-3.5 w-3.5" /> 查看提示
          </Button>
        )}
        <Button
          size="sm"
          className="h-8 gap-1 rounded-lg bg-gradient-to-r from-amber-500 to-orange-500 text-xs text-white"
          onClick={onNext}
        >
          <ChevronRight className="h-3.5 w-3.5" /> 继续引导
        </Button>
      </div>
    </GlassCard>
  )
}
