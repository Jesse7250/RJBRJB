/**
 * 需求：认知风格差异化渲染组件（C5）。
 * 功能：
 *   - 根据文字型 / 视觉型 / 听觉型三种认知风格切换资源呈现方式；
 *   - 📖 文字型：纯讲义 Markdown 文本，干净无干扰；
 *   - 👁 视觉型：讲义上方嵌入 B站讲解视频，视频下方保留讲义文本；
 *   - 👂 听觉型：展示讲解稿 + 朗读按钮，使用浏览器 TTS 语音合成朗读；
 *   - 保留动觉型兼容（代码实操导向）。
 *
 * TODO:
 * - [已完成] 风格切换器与三种渲染模式
 * - [已完成] 浏览器 TTS 朗读支持（含语速/暂停/恢复）
 * - [已完成] 视觉型 B站视频嵌入播放器
 * - [待完成] 视频随知识点自动切换（目前先用变量与赋值一个知识点）
 * - [待完成] 与后端画像 cognitive_modality 自动联动
 */
import { useCallback, useEffect, useRef, useState } from 'react'
import { AudioLines, BookOpenText, Hand, Lightbulb, Loader2, MonitorPlay, Pause, RotateCcw, Volume2 } from 'lucide-react'

import { Button } from '@/components/ui/button'
import { cn } from '@/lib/utils'
import { ttsApi } from '@/services/api'

export type CognitiveStyle = 'text' | 'visual' | 'auditory' | 'kinesthetic'

interface Props {
  currentStyle?: CognitiveStyle
  onStyleChange?: (style: CognitiveStyle) => void
  audioText?: string
  concept?: string
  children: React.ReactNode
}

// ─── 知识点 → B站视频映射 ───
const CONCEPT_VIDEOS: Record<string, { bvid: string; title: string; page?: number }> = {
  '变量与赋值': { bvid: 'BV1dGmMBAE6h', title: '变量与赋值·动画讲解（零基础）', page: 2 },
  '变量': { bvid: 'BV1dGmMBAE6h', title: '变量与赋值·动画讲解（零基础）', page: 2 },
}

function resolveVideo(concept?: string) {
  if (!concept) return null
  if (concept && CONCEPT_VIDEOS[concept]) return CONCEPT_VIDEOS[concept]
  const matchedKey = Object.keys(CONCEPT_VIDEOS).find((key) => concept.includes(key) || key.includes(concept))
  return matchedKey ? CONCEPT_VIDEOS[matchedKey] : null
}

// ─── 风格切换按钮组 ───
const STYLES: { key: CognitiveStyle; label: string; icon: React.ElementType; desc: string }[] = [
  { key: 'text', label: '文字型', icon: BookOpenText, desc: '纯讲义文本' },
  { key: 'visual', label: '视觉型', icon: MonitorPlay, desc: '视频 + 讲义' },
  { key: 'auditory', label: '听觉型', icon: AudioLines, desc: '朗读讲解' },
  { key: 'kinesthetic', label: '动觉型', icon: Hand, desc: '动手 + 代码' },
]

export function CognitiveStyleToggle({
  currentStyle = 'text',
  onStyleChange,
}: {
  currentStyle?: CognitiveStyle
  onStyleChange?: (style: CognitiveStyle) => void
}) {
  return (
    <div className="flex items-center gap-1 rounded-xl border border-slate-200/80 bg-white/70 p-1 shadow-sm backdrop-blur-sm">
      {STYLES.map((s) => {
        const Icon = s.icon
        const active = currentStyle === s.key
        return (
          <button
            key={s.key}
            onClick={() => onStyleChange?.(s.key)}
            className={cn(
              'flex items-center gap-1.5 rounded-lg px-2.5 py-1.5 text-xs font-semibold transition-all',
              active
                ? 'bg-gradient-to-r from-indigo-500 to-violet-600 text-white shadow-md'
                : 'text-slate-500 hover:bg-white hover:text-slate-800'
            )}
            title={s.desc}
          >
            <Icon className="h-3.5 w-3.5" />
            <span className="hidden sm:inline">{s.label}</span>
          </button>
        )
      })}
    </div>
  )
}

// ─── 视觉型：B站视频播放器 ───
export function BilibiliVideoPlayer({ concept }: { concept?: string }) {
  const video = resolveVideo(concept)
  if (!video) {
    return (
      <div className="resource-video-panel resource-video-empty">
        <div className="resource-video-header">
          <span className="resource-video-icon"><MonitorPlay className="h-4 w-4" /></span>
          <div>
            <p>暂无相关视频</p>
            <small>{concept ? `「${concept}」的视频讲解正在准备中` : '请选择知识点后查看视频讲解'}</small>
          </div>
          <em>敬请期待</em>
        </div>
        <div className="resource-video-empty-body">
          <MonitorPlay className="h-10 w-10" />
          <strong>暂无相关视频，敬请期待</strong>
          <span>你可以先阅读下方讲义，或切换到听觉型让数字人按讲义讲解。</span>
        </div>
      </div>
    )
  }
  return (
    <div className="resource-video-panel">
      <div className="resource-video-header">
        <span className="resource-video-icon"><MonitorPlay className="h-4 w-4" /></span>
        <div>
          <p>{video.title}</p>
          <small>来源：Bilibili · {concept || 'Python 入门'}</small>
        </div>
        <em>讲解视频</em>
      </div>
      <div className="resource-video-frame">
        <iframe
          src={`https://player.bilibili.com/player.html?bvid=${video.bvid}&page=${video.page || 1}&high_quality=1&autoplay=0`}
          scrolling="no"
          frameBorder="no"
          allowFullScreen
          className="absolute inset-0 h-full w-full"
          title={video.title}
          sandbox="allow-scripts allow-same-origin allow-popups allow-presentation"
        />
      </div>
      <div className="resource-video-note">
        <Lightbulb className="h-3.5 w-3.5" />
        <span>看完视频后，下方讲义会继续保留，方便复盘重点。</span>
      </div>
    </div>
  )
}

// ─── 听觉型：增强 TTS 朗读器 ───
function formatAudioTime(value: number) {
  if (!Number.isFinite(value) || value <= 0) return '00:00'
  const minutes = Math.floor(value / 60)
  const seconds = Math.floor(value % 60)
  return `${String(minutes).padStart(2, '0')}:${String(seconds).padStart(2, '0')}`
}

function rateToLabel(rate: number) {
  return `${rate % 1 === 0 ? rate.toFixed(0) : rate}x`
}

type AudioCacheEntry = {
  script: string
  scriptFallback: boolean
  blob: Blob
}

const AUDIO_CACHE_LIMIT = 8
const audioCache = new Map<string, AudioCacheEntry>()
const audioPendingCache = new Map<string, Promise<AudioCacheEntry>>()

function makeAudioCacheKey(text: string, concept?: string) {
  const source = `${concept || 'current'}::${text.length}::${text.slice(0, 180)}::${text.slice(-120)}`
  let hash = 0
  for (let i = 0; i < source.length; i += 1) {
    hash = (hash * 31 + source.charCodeAt(i)) >>> 0
  }
  return `${concept || 'current'}:${text.length}:${hash.toString(36)}`
}

function rememberAudio(key: string, entry: AudioCacheEntry) {
  audioCache.delete(key)
  audioCache.set(key, entry)
  while (audioCache.size > AUDIO_CACHE_LIMIT) {
    const oldestKey = audioCache.keys().next().value
    if (!oldestKey) break
    audioCache.delete(oldestKey)
  }
}

function forgetAudio(key: string) {
  audioCache.delete(key)
}

export function TTSReader({ text, concept }: { text: string; concept?: string }) {
  const [script, setScript] = useState('')
  const [scriptFallback, setScriptFallback] = useState(false)
  const [scriptStatus, setScriptStatus] = useState<'idle' | 'generating' | 'ready' | 'error'>('idle')
  const [audioStatus, setAudioStatus] = useState<'idle' | 'generating' | 'ready' | 'error'>('idle')
  const [playing, setPlaying] = useState(false)
  const [rate, setRate] = useState(1)
  const [duration, setDuration] = useState(0)
  const [currentTime, setCurrentTime] = useState(0)
  const [error, setError] = useState('')
  const audioRef = useRef<HTMLAudioElement | null>(null)
  const audioUrlRef = useRef('')
  const rateRef = useRef(rate)

  useEffect(() => {
    rateRef.current = rate
    if (audioRef.current) audioRef.current.playbackRate = rate
  }, [rate])

  const clearAudio = useCallback(() => {
    if (audioRef.current) {
      audioRef.current.onloadedmetadata = null
      audioRef.current.ontimeupdate = null
      audioRef.current.onplay = null
      audioRef.current.onpause = null
      audioRef.current.onended = null
      audioRef.current.onerror = null
      audioRef.current.pause()
      audioRef.current.src = ''
      audioRef.current = null
    }
    if (audioUrlRef.current) {
      URL.revokeObjectURL(audioUrlRef.current)
      audioUrlRef.current = ''
    }
    setPlaying(false)
    setDuration(0)
    setCurrentTime(0)
  }, [])

  const loadAudioEntry = useCallback((entry: AudioCacheEntry) => {
    if (audioUrlRef.current) {
      URL.revokeObjectURL(audioUrlRef.current)
      audioUrlRef.current = ''
    }
    const url = URL.createObjectURL(entry.blob)
    audioUrlRef.current = url
    const audio = new Audio(url)
    audio.preload = 'auto'
    audio.playbackRate = rateRef.current
    audio.onloadedmetadata = () => setDuration(Number.isFinite(audio.duration) ? audio.duration : 0)
    audio.ontimeupdate = () => setCurrentTime(audio.currentTime)
    audio.onplay = () => setPlaying(true)
    audio.onpause = () => setPlaying(false)
    audio.onended = () => {
      setPlaying(false)
      setCurrentTime(audio.duration || 0)
    }
    audio.onerror = () => {
      setAudioStatus('error')
      setPlaying(false)
      setError('语音文件播放失败，请稍后重试或重新生成。')
    }
    audioRef.current = audio
    audio.load()
    setAudioStatus('ready')
  }, [])

  const generateAudio = useCallback(async (force = false) => {
    const sourceText = text.trim()
    if (!sourceText) return
    const cacheKey = makeAudioCacheKey(sourceText, concept)

    clearAudio()
    if (force) forgetAudio(cacheKey)
    setError('')
    setScript('')
    setScriptFallback(false)
    setScriptStatus('generating')
    setAudioStatus('generating')

    try {
      const cached = !force ? audioCache.get(cacheKey) : null
      let entry = cached || null
      if (!entry) {
        let pending = !force ? audioPendingCache.get(cacheKey) : null
        if (!pending) {
          pending = (async () => {
            const scriptResponse = await ttsApi.teachingScript(sourceText, concept)
            const nextScript = (scriptResponse.data?.script || '').trim()
            const finalScript = nextScript || sourceText.slice(0, 760)
            const audioResponse = await ttsApi.synthesize(finalScript.slice(0, 780), 50, 'x4_xiaoyan')
            const blob = audioResponse.data as Blob
            if (!blob || blob.size < 128) throw new Error('后端没有返回有效语音文件')
            return {
              script: finalScript,
              scriptFallback: Boolean(scriptResponse.data?.fallback),
              blob,
            }
          })()
          audioPendingCache.set(cacheKey, pending)
          pending.finally(() => audioPendingCache.delete(cacheKey))
        }
        entry = await pending
        rememberAudio(cacheKey, entry)
      }

      setScript(entry.script)
      setScriptFallback(entry.scriptFallback)
      setScriptStatus('ready')
      loadAudioEntry(entry)
    } catch (err) {
      setAudioStatus('error')
      setScriptStatus((status) => (status === 'generating' ? 'error' : status))
      setError(err instanceof Error ? err.message : '讲解语音生成失败，请稍后重试。')
    }
  }, [clearAudio, concept, loadAudioEntry, text])

  useEffect(() => {
    generateAudio()
    return clearAudio
  }, [clearAudio, generateAudio])

  const togglePlay = useCallback(async () => {
    const audio = audioRef.current
    if (!audio || audioStatus !== 'ready') return
    if (playing) {
      audio.pause()
      return
    }
    if (duration > 0 && audio.currentTime >= duration - 0.1) {
      audio.currentTime = 0
      setCurrentTime(0)
    }
    try {
      await audio.play()
    } catch {
      setError('浏览器阻止了自动播放，请再次点击朗读讲解。')
    }
  }, [audioStatus, duration, playing])

  const seekTo = useCallback((value: number) => {
    const audio = audioRef.current
    if (!audio || audioStatus !== 'ready') return
    audio.currentTime = value
    setCurrentTime(value)
  }, [audioStatus])

  if (!text) {
    return <div className="resource-audio-empty">当前资源暂无讲解稿，请先生成资源或切换到其他知识点。</div>
  }

  const generating = scriptStatus === 'generating' || audioStatus === 'generating'
  const ready = audioStatus === 'ready'
  const progressMax = duration || 100
  const progressValue = duration ? Math.min(currentTime, duration) : 0

  return (
    <div className="resource-audio-panel">
      <div className="resource-audio-controls">
        <Button
          variant="outline"
          size="sm"
          className={cn('resource-audio-button', playing && 'active')}
          onClick={togglePlay}
          disabled={!ready}
        >
          {generating ? <Loader2 className="h-3.5 w-3.5 animate-spin" /> : playing ? <Pause className="h-3.5 w-3.5" /> : <Volume2 className="h-3.5 w-3.5" />}
          {generating ? '正在生成讲解语音' : playing ? '暂停讲解' : '朗读讲解'}
        </Button>
        <Button variant="ghost" size="sm" className="resource-audio-ghost-button" onClick={() => generateAudio(true)} disabled={generating}>
          <RotateCcw className="h-3.5 w-3.5" />重新生成
        </Button>
        <div className="resource-audio-rate">
          {[0.75, 1, 1.25, 1.5].map((r) => (
            <button key={r} type="button" onClick={() => setRate(r)} className={cn(rate === r && 'active')}>
              {rateToLabel(r)}
            </button>
          ))}
        </div>
      </div>
      {generating && <div className="resource-audio-state active"><span /><p>正在生成老师讲解稿与语音，生成完成后即可播放。</p></div>}
      {ready && !playing && <div className="resource-audio-state paused">讲解语音已准备好 · 点击「朗读讲解」开始播放</div>}
      {playing && <div className="resource-audio-state active"><span /><p>正在讲解中 · 语速 {rateToLabel(rate)} · 可拖动进度条回听重点</p></div>}
      {error && <div className="resource-audio-state error">{error}</div>}
      <div className="resource-audio-progress">
        <span>{formatAudioTime(currentTime)}</span>
        <input
          type="range"
          min={0}
          max={progressMax}
          step={0.1}
          value={progressValue}
          disabled={!ready || !duration}
          onChange={(event) => seekTo(Number(event.target.value))}
          aria-label="讲解语音进度"
        />
        <span>{formatAudioTime(duration)}</span>
      </div>
      <div className="resource-audio-script">
        <p>{scriptFallback ? '基础讲解稿' : '老师讲解稿'}</p>
        <div>{script || '讲解稿生成中，请稍等...'}</div>
      </div>
    </div>
  )
}

// ─── 认知风格面板 ───
export function CognitiveStylePanel({
  currentStyle = 'text',
  onStyleChange,
  audioText,
  concept,
  children,
}: Props) {
  return (
    <div className={cn('relative rounded-2xl transition-colors',
      currentStyle === 'visual' && 'border border-blue-100 bg-blue-50/20',
      currentStyle === 'auditory' && 'border border-amber-100 bg-amber-50/20',
      currentStyle === 'kinesthetic' && 'border border-emerald-100 bg-emerald-50/20'
    )}>
      <div className="mb-3 flex flex-wrap items-center justify-between gap-2">
        <CognitiveStyleToggle currentStyle={currentStyle} onStyleChange={onStyleChange} />
      </div>
      {currentStyle === 'visual' && <BilibiliVideoPlayer concept={concept} />}
      {currentStyle === 'auditory' && <TTSReader text={audioText || ''} concept={concept} />}
      {currentStyle === 'kinesthetic' && (
        <div className="mb-4 rounded-xl border border-emerald-200 bg-emerald-50/70 p-3 text-xs font-semibold text-emerald-800">
          💡 动觉学习模式：建议先阅读代码案例，然后自己动手修改并运行，最后再回看讲解。
        </div>
      )}
      <div className={cn('transition-opacity', currentStyle === 'auditory' ? 'opacity-90' : 'opacity-100')}>
        {children}
      </div>
    </div>
  )
}
