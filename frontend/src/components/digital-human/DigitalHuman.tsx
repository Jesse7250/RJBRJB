/**
 * 数字人教师组件
 * - 大尺寸 SVG 教师形象 + 旋转光环
 * - 待机：呼吸缩放 + 光环慢转
 * - 朗读：脉冲发光 + 光环加速 + 声波纹扩散 + 底部音律条跳动
 * - 优先使用讯飞 TTS，不可用时回退浏览器语音
 */
import { useState } from 'react'
import { motion } from 'framer-motion'
import { Gauge, Radio, Volume2, VolumeX } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { cn } from '@/lib/utils'
import { useSparkTTS } from '@/components/digital-human/useSparkTTS'
import { ttsApi } from '@/services/api'

interface DigitalHumanProps { text: string; concept?: string; className?: string }

function buildTeachingScript(rawText: string, concept?: string) {
  const cleaned = rawText
    .replace(/```[\s\S]*?```/g, '这里有一段示例代码，可以先看结构，再关注变量和输出结果。')
    .replace(/`([^`]+)`/g, '$1')
    .replace(/!\[[^\]]*]\([^)]*\)/g, '')
    .replace(/\[[^\]]+]\([^)]*\)/g, '')
    .split('\n')
    .map((line) => line.trim())
    .filter(Boolean)
    .map((line) => {
      const heading = line.match(/^#{1,6}\s*(.+)$/)
      if (heading) return `接下来我们看${heading[1]}。`
      return line
        .replace(/^[-*+]\s+/, '这里有一个要点：')
        .replace(/^\d+[.)、]\s+/, '第一个需要注意的是，')
        .replace(/\*\*/g, '')
        .replace(/__/g, '')
        .replace(/[>#|]/g, ' ')
    })
    .join(' ')
    .replace(/\s+/g, ' ')
    .trim()

  if (!cleaned) return ''
  const intro = concept
    ? `这节课我们围绕${concept}来学习。我会按照讲义内容，用老师讲课的方式帮你梳理重点。`
    : '这节课我会按照讲义内容，用老师讲课的方式帮你梳理重点。'
  return `${intro} ${cleaned}`.slice(0, 1800)
}

function MouthBars({ active }: { active: boolean }) {
  const bars = [0, 1, 2, 3, 4, 5, 6]
  return (
    <div className="flex items-end justify-center gap-1.5 h-8">
      {bars.map((i) => (
        <motion.span key={i} className="block w-[6px] rounded-full bg-gradient-to-t from-amber-500 to-yellow-300"
          animate={active ? { height: [4, 8 + i * 3, 14 + i * 2, 6, 16 + i * 2, 4], opacity: [0.5, 1, 0.8, 1, 0.6, 0.5] } : { height: 3, opacity: 0.3 }}
          transition={active ? { duration: 0.55 + i * 0.07, repeat: Infinity, repeatType: 'reverse', ease: 'easeInOut', delay: i * 0.05 } : { duration: 0.3 }} />
      ))}
    </div>
  )
}

function SoundRings({ active }: { active: boolean }) {
  return (
    <div className="absolute inset-0 flex items-center justify-center pointer-events-none" style={{ width: 200, height: 200, left: '50%', top: '50%', transform: 'translate(-50%, -50%)' }}>
      {[1, 2, 3].map((i) => (
        <motion.div key={i} className="absolute rounded-full border-2 border-amber-400/50"
          animate={active ? { width: [100, 180 + i * 20, 100], height: [100, 180 + i * 20, 100], opacity: [0.5, 0, 0.5] } : { width: 100, height: 100, opacity: 0 }}
          transition={active ? { duration: 1.8, repeat: Infinity, delay: i * 0.6, ease: 'easeOut' } : { duration: 0.5 }} />
      ))}
    </div>
  )
}

export function DigitalHuman({ text, concept, className }: DigitalHumanProps) {
  const { speaking, sparkAvailable, speak: ttsSpeak, stop: ttsStop } = useSparkTTS()
  const [rate, setRate] = useState(1)
  const [preparing, setPreparing] = useState(false)
  const [scriptCache, setScriptCache] = useState<{ key: string; script: string } | null>(null)
  const teachingScript = buildTeachingScript(text, concept)
  const sourceLabel = sparkAvailable ? '讯飞超拟人 TTS' : '浏览器语音'
  const sourceDesc = sparkAvailable === null
    ? '正在检测语音服务'
    : sparkAvailable
      ? '已连接高质量合成语音'
      : '本机浏览器朗读，后端配置讯飞后会自动切换'
  // 界面倍速 → API speed (0-100)
  const toApiSpeed = (r: number) => r === 0.5 ? 25 : r === 2 ? 100 : 50
  const scriptKey = `${concept || ''}:${text.length}:${text.slice(0, 120)}`

  const getTeacherScript = async () => {
    if (!text.trim()) return teachingScript || text
    if (scriptCache?.key === scriptKey) return scriptCache.script
    setPreparing(true)
    try {
      const response = await ttsApi.teachingScript(text, concept)
      const script = response.data?.script?.trim() || teachingScript || text
      setScriptCache({ key: scriptKey, script })
      return script
    } catch {
      const script = teachingScript || text
      setScriptCache({ key: scriptKey, script })
      return script
    } finally {
      setPreparing(false)
    }
  }

  const handleSpeak = async () => {
    if (speaking) { ttsStop(); return }
    const script = await getTeacherScript()
    ttsSpeak(script, toApiSpeed(rate))
  }

  const handleRateChange = async (r: number) => {
    setRate(r)
    if (speaking) {
      ttsStop()
      const script = await getTeacherScript()
      setTimeout(() => ttsSpeak(script, toApiSpeed(r)), 150)
    }
  }

  return (
    <div className={cn('flex flex-col items-center py-4', className)}>
      {/* TTS 来源标记 */}
      <div className={cn('digital-human-source-card', sparkAvailable && 'spark-ready')}>
        <span className="digital-human-source-icon"><Radio className="h-3.5 w-3.5" /></span>
        <div>
          <strong>当前音源：{sparkAvailable === null ? '检测中' : sourceLabel}</strong>
          <small>{sourceDesc}</small>
        </div>
      </div>

      {/* 形象区 */}
      <div className="digital-human-orb">
        <SoundRings active={speaking} />
        <motion.div className="digital-human-core"
          animate={speaking ? { scale: [1, 1.06, 0.98, 1.04, 1], boxShadow: ['0 0 20px rgba(251,191,36,0.3)', '0 0 50px rgba(251,191,36,0.6)', '0 0 30px rgba(251,191,36,0.4)', '0 0 55px rgba(251,191,36,0.5)', '0 0 20px rgba(251,191,36,0.3)'] } : { scale: [1, 1.02, 1], boxShadow: '0 0 15px rgba(251,191,36,0.15)' }}
          transition={speaking ? { duration: 1.2, repeat: Infinity, ease: 'easeInOut' } : { duration: 4, repeat: Infinity, ease: 'easeInOut' }}>
          <motion.div className="digital-human-ring primary"
            animate={{ rotate: 360 }} transition={{ duration: speaking ? 2 : 10, repeat: Infinity, ease: 'linear' }} />
          <motion.div className="digital-human-ring secondary"
            animate={{ rotate: -360 }} transition={{ duration: speaking ? 3.5 : 14, repeat: Infinity, ease: 'linear' }} />
          <svg viewBox="0 0 120 120" className="digital-human-hive-mark" fill="none" aria-hidden="true">
            <path d="M60 10 95 30v40L60 90 25 70V30L60 10Z" fill="url(#hiveFill)" stroke="#f6a21a" strokeWidth="3" />
            <path d="M60 24 82 37v26L60 76 38 63V37L60 24Z" fill="#ffffff" stroke="#08a99a" strokeWidth="2" />
            <path d="M60 39 72 46v14L60 67 48 60V46L60 39Z" fill="#fff4df" stroke="#f6a21a" strokeWidth="2" />
            <path d="M44 28 28 37v18l16 9M76 28l16 9v18l-16 9" stroke="#bfdee8" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
            <path d="M53 54h14" stroke="#07897d" strokeWidth="3" strokeLinecap="round" />
            <motion.path
              d="M42 82c10 8 26 8 36 0"
              stroke="#08a99a"
              strokeWidth="3"
              strokeLinecap="round"
              animate={speaking ? { pathLength: [0.35, 1, 0.35], opacity: [0.45, 1, 0.45] } : { pathLength: 0.65, opacity: 0.65 }}
              transition={{ duration: 1.1, repeat: speaking ? Infinity : 0, ease: 'easeInOut' }}
            />
            <motion.path
              d="M34 94c15 10 37 10 52 0"
              stroke="#f6a21a"
              strokeWidth="3"
              strokeLinecap="round"
              animate={speaking ? { pathLength: [0.25, 1, 0.25], opacity: [0.35, 0.9, 0.35] } : { pathLength: 0.55, opacity: 0.55 }}
              transition={{ duration: 1.35, repeat: speaking ? Infinity : 0, ease: 'easeInOut' }}
            />
            <defs>
              <linearGradient id="hiveFill" x1="25" y1="12" x2="96" y2="88">
                <stop stopColor="#fff4df" />
                <stop offset="0.48" stopColor="#f6d36f" />
                <stop offset="1" stopColor="#f6a21a" />
              </linearGradient>
            </defs>
          </svg>
        </motion.div>
      </div>

      <div className="-mt-2 mb-3"><MouthBars active={speaking} /></div>

      <motion.div className="mb-4 text-sm font-bold" animate={{ color: speaking ? '#059669' : '#94a3b8' }}>
        {preparing ? '正在生成老师讲解稿...' : speaking ? '正在讲解...' : '点击按钮开始'}
      </motion.div>

      <div className="flex flex-wrap items-center justify-center gap-2">
        <Button type="button" size="sm" className={cn('h-10 gap-1.5 rounded-xl text-sm font-bold min-w-[120px] transition-all', speaking ? 'bg-emerald-500 text-white hover:bg-emerald-600 shadow-lg shadow-emerald-500/30' : 'bg-amber-500 text-white hover:bg-amber-600 shadow-lg shadow-amber-500/30')}
          disabled={preparing}
          onClick={handleSpeak}>
          {speaking ? <VolumeX className="h-4 w-4" /> : <Volume2 className="h-4 w-4" />}
          {preparing ? '生成讲解稿中' : speaking ? '停止' : '朗读讲解'}
        </Button>
      </div>

      <div className="digital-human-rate-control">
        <span><Gauge className="h-3.5 w-3.5" />语速</span>
        {[0.5, 1, 2].map((r) => (
          <button key={r} type="button" onClick={() => handleRateChange(r)}
            className={cn(rate === r && 'active')}>{r}x</button>
        ))}
      </div>

      {concept && <p className="mt-3 text-xs text-slate-400">讲解知识点：<span className="font-bold text-slate-600">{concept}</span></p>}
    </div>
  )
}
