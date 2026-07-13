import { useEffect, useState } from 'react'
import { AudioLines, BarChart3, BookOpenText, ChevronDown, ChevronUp, MonitorPlay, Route } from 'lucide-react'
import { cn } from '@/lib/utils'
import type { LearningEvent, LearningPlanResponse, ResourceVersion, ThinkingStep } from '@/services/api'
import type { NavKey } from './types'

type StyleMode = 'text' | 'visual' | 'auditory' | 'kinesthetic'

const STYLE_OPTIONS: Array<{
  key: Exclude<StyleMode, 'kinesthetic'>
  label: string
  desc: string
  Icon: typeof BookOpenText
}> = [
  { key: 'text', label: '文字型', desc: '精读讲义', Icon: BookOpenText },
  { key: 'visual', label: '视觉型', desc: '视频讲解', Icon: MonitorPlay },
  { key: 'auditory', label: '听觉型', desc: '语音讲解', Icon: AudioLines },
]

const STYLE_COPY: Record<StyleMode, string> = {
  text: '文字型：以讲义文本为主，适合连续阅读和复盘。',
  visual: '视觉型：播放教学视频并保留讲义，适合先看示范再阅读。',
  auditory: '听觉型：使用数字人朗读讲解稿，适合边听边记。',
  kinesthetic: '动觉型：强调代码练习、即时运行和操作反馈。',
}

const TITLE_BY_NAV: Record<NavKey, string> = {
  profile: '学习画像工作区',
  graph: '路径规划工作区',
  resources: '学习资源工作区',
  chat: '对话辅导工作区',
  code: '代码沙箱工作区',
  progress: '掌握进度工作区',
}

export function WorkspaceDock({
  activeNav,
  selectedConcept,
  styleMode,
  workspaceNote,
  thinkingSteps,
  versions,
  learningPlan,
  learningEvents,
  onStyleChange,
  onAnalyze,
  onPlanPath,
}: {
  activeNav: NavKey
  selectedConcept: string
  styleMode: StyleMode
  workspaceNote: string
  thinkingSteps: ThinkingStep[]
  versions: ResourceVersion[]
  learningPlan?: LearningPlanResponse | null
  learningEvents?: LearningEvent[]
  onStyleChange: (mode: StyleMode) => void
  onAnalyze: () => void
  onPlanPath: () => void
}) {
  const isVerticalDock = activeNav === 'profile' || activeNav === 'chat'
  const [collapsed, setCollapsed] = useState(!isVerticalDock)

  useEffect(() => {
    setCollapsed(!isVerticalDock)
  }, [isVerticalDock])

  const fallbackSteps: ThinkingStep[] = [
    { agent: 'Navigator', stage: 'path', message: '选择知识节点后可规划学习路径。' },
    { agent: 'Builder', stage: 'resource', message: '可为当前目标或指定节点生成学习资源。' },
    { agent: 'Evaluator', stage: 'analysis', message: '学习行为会联动掌握度分析与画像更新。' },
  ]

  return (
    <div className={cn('workspace-dock', collapsed && 'collapsed')}>
      <div className="workspace-summary">
        <div className="workspace-title-row">
          <p className="workspace-eyebrow">{TITLE_BY_NAV[activeNav]}</p>
          <button
            type="button"
            className="workspace-toggle"
            onClick={() => setCollapsed((value) => !value)}
            aria-expanded={!collapsed}
          >
            {collapsed ? <ChevronUp className="h-4 w-4" /> : <ChevronDown className="h-4 w-4" />}
            <span>{collapsed ? '展开' : '收起'}</span>
          </button>
        </div>
        <h3>{selectedConcept}</h3>
        <span>{workspaceNote}</span>
      </div>

      {!collapsed && (
        <div className="style-switcher" aria-label="学习呈现模式">
          <div className="style-switcher-tabs">
            {STYLE_OPTIONS.map(({ key, label, desc, Icon }) => {
              const active = styleMode === key
              return (
                <button
                  key={key}
                  type="button"
                  onClick={() => onStyleChange(key)}
                  className={cn(active && 'active')}
                  aria-pressed={active}
                  title={`${label}：${desc}`}
                >
                  <span className="style-mode-icon" aria-hidden="true">
                    <Icon className="h-4 w-4" />
                  </span>
                  <span className="style-mode-copy">
                    <strong>{label}</strong>
                    <small>{desc}</small>
                  </span>
                </button>
              )
            })}
          </div>
          <span className="style-mode-note">{STYLE_COPY[styleMode]}</span>
        </div>
      )}

      {!collapsed && (
        <div className="dock-actions">
          <button type="button" onClick={onPlanPath}>
            <Route className="h-4 w-4" />
            <span>规划路径</span>
          </button>
          <button type="button" onClick={onAnalyze}>
            <BarChart3 className="h-4 w-4" />
            <span>分析掌握度</span>
          </button>
        </div>
      )}

      {!collapsed && (
        <div className="dock-feed">
          {(thinkingSteps.length > 0 ? thinkingSteps : fallbackSteps).slice(0, 3).map((step, index) => (
            <p key={`${step.agent}-${index}`}>
              <strong>{step.agent}</strong>
              <span>{step.message}</span>
            </p>
          ))}
          {versions.length > 0 && (
            <p>
              <strong>Furnace</strong>
              <span>已读取 {versions.length} 个资源版本演进记录。</span>
            </p>
          )}
          {learningPlan?.plan?.length ? (
            <p>
              <strong>Plan</strong>
              <span>
                后端规划 {learningPlan.plan.length} 个节点，预计 {learningPlan.total_minutes} 分钟：
                {learningPlan.plan.slice(0, 3).map((item) => item.concept).join(' -> ')}
              </span>
            </p>
          ) : null}
          {learningEvents?.[0] ? (
            <p>
              <strong>Event</strong>
              <span>
                最近行为：{learningEvents[0].event_type}
                {learningEvents[0].concept ? ` · ${learningEvents[0].concept}` : ''}
              </span>
            </p>
          ) : null}
        </div>
      )}

    </div>
  )
}
