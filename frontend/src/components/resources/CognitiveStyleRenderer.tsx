/**
 * 需求：认知风格差异化渲染组件（C5）。
 * 功能：
 *   - 根据视觉型 / 听觉型 / 动觉型三种认知风格切换资源呈现方式；
 *   - 视觉型：默认 Markdown + 导图；
 *   - 听觉型：突出音频文本、支持浏览器 TTS 朗读；
 *   - 动觉型：突出代码案例与练习，鼓励动手实践。
 *
 * TODO:
 * - [已完成] 风格切换器与三种渲染模式
 * - [已完成] 浏览器 TTS 朗读支持
 * - [待完成] 与后端画像 cognitive_modality 自动联动
 */
import { useEffect, useState } from 'react'
import { Eye, Ear, Hand, Volume2, VolumeX } from 'lucide-react'

import { Button } from '@/components/ui/button'
import { cn } from '@/lib/utils'

export type CognitiveStyle = 'visual' | 'auditory' | 'kinesthetic'

interface Props {
  currentStyle?: CognitiveStyle
  onStyleChange?: (style: CognitiveStyle) => void
  audioText?: string
  children: React.ReactNode
}

const STYLES: { key: CognitiveStyle; label: string; icon: React.ElementType; desc: string }[] = [
  { key: 'visual', label: '视觉型', icon: Eye, desc: '图文 + 导图' },
  { key: 'auditory', label: '听觉型', icon: Ear, desc: '朗读 + 讲解' },
  { key: 'kinesthetic', label: '动觉型', icon: Hand, desc: '动手 + 代码' },
]

export function CognitiveStyleToggle({
  currentStyle = 'visual',
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

export function CognitiveStylePanel({
  currentStyle = 'visual',
  onStyleChange,
  audioText,
  children,
}: Props) {
  const [speaking, setSpeaking] = useState(false)

  // 组件卸载时停止 TTS
  useEffect(() => {
    const synth = window.speechSynthesis
    return () => {
      synth?.cancel()
    }
  }, [])

  const toggleSpeak = () => {
    const synth = window.speechSynthesis
    if (!synth) return
    if (speaking) {
      synth.cancel()
      setSpeaking(false)
      return
    }
    const text = audioText || (typeof children === 'string' ? children : '')
    if (!text) return
    const utter = new SpeechSynthesisUtterance(text)
    utter.lang = 'zh-CN'
    utter.onend = () => setSpeaking(false)
    synth.speak(utter)
    setSpeaking(true)
  }

  return (
    <div
      className={cn(
        'relative rounded-2xl transition-colors',
        currentStyle === 'auditory' && 'border border-amber-100 bg-amber-50/30',
        currentStyle === 'kinesthetic' && 'border border-emerald-100 bg-emerald-50/30'
      )}
    >
      <div className="mb-3 flex flex-wrap items-center justify-between gap-2">
        <CognitiveStyleToggle currentStyle={currentStyle} onStyleChange={onStyleChange} />
        {currentStyle === 'auditory' && (
          <Button
            variant="outline"
            size="sm"
            className="h-8 gap-1 rounded-lg text-xs"
            onClick={toggleSpeak}
          >
            {speaking ? <VolumeX className="h-3.5 w-3.5" /> : <Volume2 className="h-3.5 w-3.5" />}
            {speaking ? '停止朗读' : '朗读讲解'}
          </Button>
        )}
      </div>

      {currentStyle === 'auditory' && audioText && (
        <div className="mb-4 rounded-xl border border-amber-100 bg-white/70 p-4 text-sm leading-relaxed text-slate-700 backdrop-blur-sm">
          <span className="mb-1 block text-xs font-bold text-amber-700">音频版讲解</span>
          {audioText}
        </div>
      )}

      {currentStyle === 'kinesthetic' && (
        <div className="mb-4 rounded-xl border border-emerald-100 bg-emerald-50/70 p-3 text-xs font-semibold text-emerald-800">
          💡 动觉学习模式：建议先阅读代码案例，然后自己动手修改并运行，最后再回看讲解。
        </div>
      )}

      <div
        className={cn(
          'transition-opacity',
          currentStyle === 'auditory' ? 'opacity-90' : 'opacity-100'
        )}
      >
        {children}
      </div>
    </div>
  )
}
