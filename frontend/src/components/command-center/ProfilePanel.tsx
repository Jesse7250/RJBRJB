import { useEffect, useState } from 'react'
import { motion } from 'framer-motion'
import { UserRound } from 'lucide-react'
import { sessionApi, type EvidenceItem, type SessionResponse } from '@/services/api'
import { Panel, PanelHeader } from './Panel'
import { cn } from '@/lib/utils'
import type { SessionStats } from './types'

function ProfileLine({
  label,
  value,
  blocks,
  spark,
}: {
  label: string
  value: string
  blocks?: number
  spark?: boolean
}) {
  return (
    <div className="profile-line">
      <span>{label}</span>
      <div>
        <strong>{value}</strong>
        {blocks && (
          <span className="flex gap-1">
            {Array.from({ length: 8 }).map((_, index) => (
              <i key={index} className={cn('h-2.5 w-3 rounded-sm bg-white/12', index < blocks + 2 && 'bg-emerald-300')} />
            ))}
          </span>
        )}
        {spark && <span className="spark-line" />}
      </div>
    </div>
  )
}

export function ProfilePanel({
  session,
  masteredCount,
  targetConcept,
  stats,
  totalConcepts,
}: {
  session: SessionResponse | null
  masteredCount: number
  targetConcept: string
  stats: SessionStats | null
  totalConcepts: number
}) {
  const profile = session?.profile
  const [expanded, setExpanded] = useState(false)
  const [evidence, setEvidence] = useState<Record<string, EvidenceItem[]>>({})
  const [evidenceOpen, setEvidenceOpen] = useState(false)
  const [confidence, setConfidence] = useState(0)
  const hasModalityEvidence = Boolean(evidence.cognitive_modality?.length)
  const hasPaceEvidence = Boolean(evidence.learning_pace?.length)
  const rawModality = profile?.cognitive_modality
  const modality = !hasModalityEvidence && rawModality === 'visual'
    ? '待校准'
    : rawModality === 'text' ? '文字型' : rawModality === 'visual' ? '视觉型' : rawModality === 'auditory' ? '听觉型' : rawModality === 'kinesthetic' ? '实践型' : '待校准'
  const paceLabel = !hasPaceEvidence ? '待校准' : profile?.learning_pace === 'fast' ? '快速推进' : profile?.learning_pace === 'slow' ? '需要放慢讲解' : '稳步推进'
  const interventionLabel = !hasPaceEvidence ? '继续观察' : profile?.learning_pace === 'fast' ? '挑战题' : profile?.learning_pace === 'slow' ? '分步讲解' : '路径巩固'
  const errorPatterns = profile?.error_patterns?.filter(Boolean) || []
  const masteredConcepts = profile?.mastered_concepts?.filter(Boolean) || []
  const knowledgeLevel = typeof profile?.knowledge_level === 'number' ? profile.knowledge_level : 1

  useEffect(() => {
    if (!session?.session_id) return
    sessionApi
      .getProfileEvidence(session.session_id)
      .then((res) => {
        setEvidence(res.data.evidence || {})
        setConfidence(res.data.confidence ?? 0)
      })
      .catch(() => {
        setEvidence({})
        setConfidence(0)
      })
  }, [session?.session_id, stats?.chat_count])

  return (
    <Panel className="profile-panel min-h-[278px]">
      <PanelHeader
        title="学习画像"
        icon={UserRound}
        meta={
          <button
            type="button"
            onClick={() => setExpanded((value) => !value)}
            className="profile-detail-toggle"
            aria-expanded={expanded}
          >
            {expanded ? '收起画像' : '详细画像'}
          </button>
        }
      />
      <div className="profile-layout">
        <div className="profile-avatar">
          <img src="/assets/student-avatar-visual.png" alt="当前学习者画像" />
          <p>当前学习者</p>
          <span>目标：{session?.target_concept || targetConcept}</span>
        </div>
        <div className="profile-summary">
          <ProfileLine label="知识水平" value={session ? `${knowledgeLevel}/5` : '待同步'} blocks={session ? knowledgeLevel : undefined} />
          <ProfileLine label="认知风格" value={modality} />
          <ProfileLine label="学习节奏" value={paceLabel} spark />
          <ProfileLine label="学习目标" value={`通过「${session?.target_concept || targetConcept}」练习`} />
          <p className="profile-mastered">已掌握 {masteredCount} 个关键节点</p>
        </div>
      </div>
      {expanded && (
        <motion.div
          className="profile-detail-grid"
          initial={{ opacity: 0, y: -8 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.2 }}
        >
          <div>
            <strong>学习偏好</strong>
            <span>{modality === '待校准' ? '继续完成学习、练习和资源浏览后，系统会逐步校准学习偏好。' : `当前更偏向${modality}学习；系统会结合后续行为继续校准。`}</span>
          </div>
          <div>
            <strong>易错模式</strong>
            <span>{errorPatterns.length ? errorPatterns.slice(0, 2).join('、') : '暂无明显易错模式'}</span>
          </div>
          <div>
            <strong>已掌握概念</strong>
            <span>{masteredConcepts.length ? masteredConcepts.slice(0, 3).join('、') : '暂无已确认掌握概念'}</span>
          </div>
        </motion.div>
      )}
      {Object.keys(evidence).length > 0 && (
        <div className="mt-4 rounded-lg border border-white/10 bg-white/5 p-3">
          <button
            type="button"
            onClick={() => setEvidenceOpen((value) => !value)}
            className="flex w-full items-center justify-between text-xs font-bold text-indigo-200"
            aria-expanded={evidenceOpen}
          >
            <span>画像证据（{Object.keys(evidence).length} 个维度）</span>
            <span>{evidenceOpen ? '收起' : '展开'}</span>
          </button>
          {evidenceOpen && (
            <motion.div
              className="mt-2 space-y-2"
              initial={{ opacity: 0, y: -4 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.2 }}
            >
              {Object.entries(evidence).map(([dim, items]) => (
                <div key={dim}>
                  <p className="text-[10px] font-bold uppercase tracking-wider text-slate-400">{dim}</p>
                  <ul className="mt-1 space-y-1">
                    {items.slice(0, 3).map((item, idx) => (
                      <li key={idx} className="text-xs text-slate-300">
                        · {item.evidence_type}
                        {item.description && <span className="text-slate-500"> — {item.description}</span>}
                      </li>
                    ))}
                  </ul>
                </div>
              ))}
            </motion.div>
          )}
        </div>
      )}
      <div className="profile-insight-strip">
        <div>
          <span>画像置信度</span>
          <strong>{session ? `${Math.round(confidence * 100)}%` : '待同步'}</strong>
        </div>
        <div>
          <span>学习轨迹</span>
          <strong>{masteredCount} / {totalConcepts > 0 ? totalConcepts : '--'}</strong>
        </div>
        <div>
          <span>推荐干预</span>
          <strong>{interventionLabel}</strong>
        </div>
      </div>
    </Panel>
  )
}
