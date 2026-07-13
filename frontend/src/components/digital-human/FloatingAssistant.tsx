import { useCallback, useEffect, useMemo, useRef, useState } from 'react'
import { AnimatePresence, motion, useDragControls, useMotionValue, type PanInfo } from 'framer-motion'
import {
  Loader2,
  Maximize2,
  MessageCircle,
  Mic,
  MicOff,
  Minimize2,
  Send,
  Sparkles,
  Volume2,
  VolumeX,
  X,
} from 'lucide-react'

import { cn } from '@/lib/utils'
import { assistantApi } from '@/services/api'
import { useSparkTTS } from '@/components/digital-human/useSparkTTS'
import { useSpeechRecognition } from '@/components/digital-human/useSpeechRecognition'
import type { NavKey } from '@/components/command-center/types'

interface Props {
  activeNav: NavKey
  selectedConcept: string
}

interface ChatMsg {
  role: 'user' | 'assistant'
  text: string
}

type AssistantGender = 'male' | 'female'
type PanelSide = 'left' | 'right'
type PanelVertical = 'top' | 'bottom'
type DockSide = 'left' | 'right'

const ASSISTANT_META: Record<AssistantGender, { name: string; image: string; voice: string; label: string }> = {
  male: {
    name: '小蜂导学助教',
    image: '/assets/eduhive-portal-assistant-cutout.png',
    voice: 'aisjiuxu',
    label: '男生',
  },
  female: {
    name: '小蜂导学学姐',
    image: '/assets/eduhive-portal-assistant-female-cutout.png',
    voice: 'aisjinger',
    label: '女生',
  },
}

const GUIDANCE: Record<NavKey, { title: string; text: string; quick: string[] }> = {
  profile: {
    title: '学习画像',
    text: '这里汇总你的知识水平、学习节奏、认知偏好和当前目标。你可以让我解释画像含义，或帮你判断下一步该补哪一块。',
    quick: ['我的画像说明了什么？', '我下一步该学什么？', '怎么提升当前目标？'],
  },
  graph: {
    title: '知识图谱',
    text: '这里展示课程知识点之间的依赖关系。你可以让我解释某个节点、规划到目标节点的路径，或说明路径为什么这样安排。',
    quick: ['解释当前节点', '帮我规划学习路径', '路径上的重点是什么？'],
  },
  resources: {
    title: '学习资源',
    text: '这里可以查看讲义、导图、练习、案例和审核报告。你可以让我用更容易理解的方式解释资源内容。',
    quick: ['总结当前讲义', '练习题怎么做？', '给我一个学习建议'],
  },
  chat: {
    title: '学习对话',
    text: '这里适合提问、追问和进行苏格拉底式引导。你可以先描述卡住的地方，我会尽量引导你自己找到答案。',
    quick: ['请引导我思考', '我哪里理解错了？', '换个例子讲讲'],
  },
  code: {
    title: '代码沙箱',
    text: '这里可以运行 Python 代码并查看输出与变量。你可以把报错或思路发给我，我会帮你定位问题。',
    quick: ['解释这段代码', '为什么运行报错？', '给我一个调试步骤'],
  },
  progress: {
    title: '掌握进度',
    text: '这里展示知识点掌握度、热力图和 BKT 分析。你可以让我解释薄弱点，或生成复习顺序。',
    quick: ['解释掌握度', '我的薄弱点在哪？', '生成复习顺序'],
  },
}

const FALLBACK_TIPS = [
  '可以把当前卡住的问题直接发给我。',
  '也可以让我解释当前页面里的按钮和数据含义。',
  '如果内容太难，我可以换一种更具体的例子讲。',
]

export function FloatingAssistant({ activeNav, selectedConcept }: Props) {
  const { speaking, source, sparkAvailable, lastError, speak: ttsSpeak, stop: ttsStop } = useSparkTTS()
  const { listening, supported: micSupported, start: startListen, stop: stopListen } = useSpeechRecognition('zh-CN')
  const [expanded, setExpanded] = useState(true)
  const [fullscreen, setFullscreen] = useState(false)
  const [dragged, setDragged] = useState(false)
  const [docked, setDocked] = useState(true)
  const [dockSide, setDockSide] = useState<DockSide>('right')
  const [panelSide, setPanelSide] = useState<PanelSide>('left')
  const [panelVertical, setPanelVertical] = useState<PanelVertical>('top')
  const [assistantGender, setAssistantGender] = useState<AssistantGender>('female')
  const [chatMessages, setChatMessages] = useState<ChatMsg[]>([])
  const [input, setInput] = useState('')
  const [loading, setLoading] = useState(false)
  const [sessionMinutes, setSessionMinutes] = useState(0)
  const [showReminder, setShowReminder] = useState(false)
  const [showTip, setShowTip] = useState(false)
  const [tipIndex, setTipIndex] = useState(0)
  const shellRef = useRef<HTMLDivElement>(null)
  const chatEndRef = useRef<HTMLDivElement>(null)
  const dragStartRef = useRef({ x: 0, y: 0 })
  const dragX = useMotionValue(0)
  const dragY = useMotionValue(0)
  const dragControls = useDragControls()

  const assistant = ASSISTANT_META[assistantGender]
  const guidance = GUIDANCE[activeNav] || GUIDANCE.resources
  const targetLabel = selectedConcept || '当前学习目标'
  const guideText = `你现在位于${guidance.title}页面，当前关注的是${targetLabel}。${guidance.text}`

  const scrollChatToBottom = useCallback((behavior: ScrollBehavior = 'smooth') => {
    requestAnimationFrame(() => {
      chatEndRef.current?.scrollIntoView({ behavior, block: 'end' })
    })
  }, [])

  const updatePanelPlacement = useCallback(() => {
    const rect = shellRef.current?.getBoundingClientRect()
    if (!rect) return
    const centerX = rect.left + rect.width / 2
    const centerY = rect.top + rect.height / 2
    setPanelSide(centerX < window.innerWidth / 2 ? 'right' : 'left')
    setPanelVertical(centerY > window.innerHeight / 2 ? 'bottom' : 'top')
  }, [])

  useEffect(() => {
    const timer = setInterval(() => setSessionMinutes((minutes) => minutes + 1), 60000)
    return () => clearInterval(timer)
  }, [])

  useEffect(() => {
    if (sessionMinutes > 0 && sessionMinutes % 30 === 0) setShowReminder(true)
  }, [sessionMinutes])

  useEffect(() => {
    const timer = setInterval(() => {
      if (!expanded) {
        setTipIndex((index) => (index + 1) % FALLBACK_TIPS.length)
        setShowTip(true)
        window.setTimeout(() => setShowTip(false), 5000)
      }
    }, 60000)
    return () => clearInterval(timer)
  }, [expanded])

  useEffect(() => {
    const frame = requestAnimationFrame(updatePanelPlacement)
    return () => cancelAnimationFrame(frame)
  }, [updatePanelPlacement])

  useEffect(() => {
    if (!expanded) return
    const handleResize = () => updatePanelPlacement()
    window.addEventListener('resize', handleResize)
    return () => window.removeEventListener('resize', handleResize)
  }, [expanded, updatePanelPlacement])

  useEffect(() => {
    if (!expanded || fullscreen) return
    const handleOutsidePointerDown = (event: PointerEvent) => {
      const target = event.target
      if (target instanceof Node && shellRef.current?.contains(target)) return
      setExpanded(false)
    }
    document.addEventListener('pointerdown', handleOutsidePointerDown)
    return () => document.removeEventListener('pointerdown', handleOutsidePointerDown)
  }, [expanded, fullscreen])

  useEffect(() => {
    scrollChatToBottom('smooth')
  }, [chatMessages, loading, scrollChatToBottom])

  useEffect(() => {
    if (!expanded) return
    scrollChatToBottom('auto')
  }, [expanded, fullscreen, scrollChatToBottom])

  const speakText = useCallback(
    (text: string) => {
      if (speaking) {
        ttsStop()
        return
      }
      console.log('[EduHive digital human voice]', {
        scope: 'floating-assistant',
        assistant: assistant.name,
        gender: assistantGender,
        voice: assistant.voice,
        source,
        sparkAvailable,
        lastError,
      })
      ttsSpeak(text, 50, assistantGender, assistant.voice)
    },
    [assistant.name, assistant.voice, assistantGender, lastError, source, sparkAvailable, speaking, ttsSpeak, ttsStop],
  )

  const sendQuestion = useCallback(
    async (question?: string) => {
      const q = (question ?? input).trim()
      if (!q || loading) return
      setInput('')
      updatePanelPlacement()
      setExpanded(true)
      setChatMessages((prev) => [...prev, { role: 'user', text: q }])
      setLoading(true)
      try {
        const response = await assistantApi.ask(q)
        const answer = response.data?.answer || '抱歉，我暂时无法回答这个问题。'
        setChatMessages((prev) => [...prev, { role: 'assistant', text: answer }])
      } catch {
        setChatMessages((prev) => [...prev, { role: 'assistant', text: '抱歉，数字人助教服务暂时不可用。' }])
      } finally {
        setLoading(false)
      }
    },
    [input, loading, updatePanelPlacement],
  )

  const handleVoiceResult = useCallback(
    (voiceText: string) => {
      setInput(voiceText)
      void sendQuestion(voiceText)
    },
    [sendQuestion],
  )

  const toggleMic = () => {
    if (listening) {
      stopListen()
      return
    }
    startListen(handleVoiceResult)
  }

  const changeGender = (gender: AssistantGender) => {
    if (speaking) ttsStop()
    setAssistantGender(gender)
  }

  const handleTriggerPointerDown = (event: React.PointerEvent) => {
    dragStartRef.current = { x: event.clientX, y: event.clientY }
    setDragged(false)
    dragControls.start(event)
  }

  const handlePointerMove = (event: React.PointerEvent) => {
    if (Math.abs(event.clientX - dragStartRef.current.x) > 3 || Math.abs(event.clientY - dragStartRef.current.y) > 3) {
      setDragged(true)
    }
  }

  const resetDockedMotion = useCallback(() => {
    dragX.set(0)
    requestAnimationFrame(() => dragX.set(0))
    window.setTimeout(() => dragX.set(0), 0)
  }, [dragX])

  const handleDragEnd = (_event: MouseEvent | TouchEvent | PointerEvent, info: PanInfo) => {
    const pointX = info.point.x
    const shouldDockLeft = pointX < 92
    const shouldDockRight = pointX > window.innerWidth - 92
    const nextDocked = shouldDockLeft || shouldDockRight

    setDocked(nextDocked)
    if (shouldDockLeft) {
      setDockSide('left')
      resetDockedMotion()
    } else if (shouldDockRight) {
      setDockSide('right')
      resetDockedMotion()
    }

    if (expanded) requestAnimationFrame(updatePanelPlacement)
  }

  const handlePointerUp = (event: React.PointerEvent) => {
    const moved = Math.abs(event.clientX - dragStartRef.current.x) > 4 || Math.abs(event.clientY - dragStartRef.current.y) > 4
    if (!moved && !dragged) {
      if (!expanded) updatePanelPlacement()
      setExpanded((value) => {
        const next = !value
        if (next) scrollChatToBottom('auto')
        return next
      })
    }
  }

  const quickQuestions = useMemo(() => guidance.quick, [guidance.quick])

  const panelContent = (
    <motion.section
      initial={{ opacity: 0, scale: 0.92, y: 16 }}
      animate={{ opacity: 1, scale: 1, y: 0 }}
      exit={{ opacity: 0, scale: 0.92, y: 16 }}
      className={cn('floating-assistant-panel', fullscreen && 'is-fullscreen')}
      onPointerDown={(event) => event.stopPropagation()}
      aria-label="数字人助教窗口"
    >
      <header className="floating-assistant-header">
        <div className="floating-assistant-avatar">
          <img className={`is-${assistantGender}`} src={assistant.image} alt={`${assistant.label}数字人助教`} draggable={false} />
          <span className={cn(speaking && 'active')} />
        </div>
        <div className="floating-assistant-title">
          <span><Sparkles className="h-3.5 w-3.5" /> 数字人助教</span>
          <strong>{assistant.name}</strong>
          <small>{guidance.title} · {targetLabel}</small>
        </div>
        <div className="floating-assistant-window-actions">
          <button type="button" onClick={() => setFullscreen((value) => !value)} title={fullscreen ? '退出大窗' : '放大窗口'}>
            {fullscreen ? <Minimize2 className="h-4 w-4" /> : <Maximize2 className="h-4 w-4" />}
          </button>
          <button type="button" onClick={() => { setExpanded(false); setFullscreen(false) }} title="收起数字人">
            <X className="h-4 w-4" />
          </button>
        </div>
      </header>

      <div className="floating-assistant-gender" role="group" aria-label="切换数字人形象">
        {(Object.keys(ASSISTANT_META) as AssistantGender[]).map((gender) => (
          <button
            key={gender}
            type="button"
            className={assistantGender === gender ? 'active' : ''}
            onClick={() => changeGender(gender)}
          >
            <img className={`is-${gender}`} src={ASSISTANT_META[gender].image} alt="" draggable={false} />
            <span>{ASSISTANT_META[gender].label}</span>
          </button>
        ))}
      </div>

      <div className="floating-assistant-guide">
        <p>{guidance.text}</p>
        <button type="button" onClick={() => speakText(guideText)}>
          {speaking ? <VolumeX className="h-3.5 w-3.5" /> : <Volume2 className="h-3.5 w-3.5" />}
          {speaking ? '停止朗读' : '朗读当前页引导'}
        </button>
      </div>

      <div className="floating-assistant-chat">
        {chatMessages.length === 0 && (
          <div className="floating-assistant-empty">
            <MessageCircle className="h-4 w-4" />
            <span>你可以问我当前页面怎么用，也可以直接描述学习中卡住的地方。</span>
          </div>
        )}
        {chatMessages.map((message, index) => (
          <div key={`${message.role}-${index}`} className={cn('floating-assistant-message', message.role)}>
            <p>{message.text}</p>
            {message.role === 'assistant' && (
              <button type="button" onClick={() => speakText(message.text)} title="朗读这条回复">
                {speaking ? <VolumeX className="h-3 w-3" /> : <Volume2 className="h-3 w-3" />}
              </button>
            )}
          </div>
        ))}
        {loading && (
          <div className="floating-assistant-thinking">
            <Loader2 className="h-3.5 w-3.5 animate-spin" />
            <span>数字人正在思考...</span>
          </div>
        )}
        <div ref={chatEndRef} />
      </div>

      {showReminder && (
        <div className="floating-assistant-reminder">
          <div>
            <strong>学习提醒</strong>
            <span>你已经学习 {sessionMinutes} 分钟，可以短暂休息后再继续。</span>
          </div>
          <button type="button" onClick={() => setShowReminder(false)}><X className="h-3.5 w-3.5" /></button>
        </div>
      )}

      <div className="floating-assistant-input">
        {listening ? (
          <div className="floating-assistant-listening">
            <i />
            <span>正在聆听...</span>
          </div>
        ) : (
          <input
            value={input}
            onChange={(event) => setInput(event.target.value)}
            onKeyDown={(event) => {
              if (event.key === 'Enter') void sendQuestion()
            }}
            placeholder={micSupported ? '打字或点麦克风提问...' : '问数字人助教任何问题...'}
          />
        )}
        {micSupported && (
          <button type="button" className={cn('mic', listening && 'active')} onClick={toggleMic} title={listening ? '停止语音输入' : '语音输入'}>
            {listening ? <MicOff className="h-4 w-4" /> : <Mic className="h-4 w-4" />}
          </button>
        )}
        <button type="button" className="send" disabled={loading || !input.trim()} onClick={() => void sendQuestion()} title="发送">
          <Send className="h-4 w-4" />
        </button>
      </div>

      <div className="floating-assistant-quick">
        {quickQuestions.map((question) => (
          <button key={question} type="button" onClick={() => void sendQuestion(question)}>
            {question}
          </button>
        ))}
      </div>
    </motion.section>
  )

  return (
    <>
      <AnimatePresence>
        {fullscreen && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="floating-assistant-backdrop"
            onClick={() => setFullscreen(false)}
          >
            <div onClick={(event) => event.stopPropagation()}>{panelContent}</div>
          </motion.div>
        )}
      </AnimatePresence>

      {!fullscreen && (
        <motion.div
          ref={shellRef}
          drag
          dragListener={false}
          dragControls={dragControls}
          dragElastic={0}
          dragMomentum={false}
          onDragEnd={handleDragEnd}
          className={cn(
            'floating-assistant-shell',
            docked ? 'is-docked' : 'is-floating',
            `dock-${dockSide}`,
            expanded && 'is-expanded',
            `panel-${panelSide}`,
            `align-${panelVertical}`,
          )}
          style={{ x: dragX, y: dragY, touchAction: 'none' }}
        >
          <AnimatePresence>
            {showTip && !expanded && (
              <motion.div
                initial={{ opacity: 0, x: 12 }}
                animate={{ opacity: 1, x: 0 }}
                exit={{ opacity: 0, x: 12 }}
                className="floating-assistant-tip"
                onPointerDown={(event) => event.stopPropagation()}
              >
                {FALLBACK_TIPS[tipIndex]}
              </motion.div>
            )}
          </AnimatePresence>

          <AnimatePresence>
            {expanded && <div className="floating-assistant-popover">{panelContent}</div>}
          </AnimatePresence>

          <button
            type="button"
            className={cn('floating-assistant-trigger', speaking && 'is-speaking')}
            aria-label="打开数字人助教"
            onPointerDown={handleTriggerPointerDown}
            onPointerMove={handlePointerMove}
            onPointerUp={handlePointerUp}
          >
            <span className="floating-assistant-trigger-image">
              <img className={`is-${assistantGender}`} src={assistant.image} alt="" draggable={false} />
            </span>
            <span className="floating-assistant-trigger-copy">
              <strong>小蜂导学</strong>
              <small>点我提问</small>
            </span>
          </button>
        </motion.div>
      )}
    </>
  )
}
