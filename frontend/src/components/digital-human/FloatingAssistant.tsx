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
  roleContext?: 'student' | 'teacher' | 'admin'
}

interface ChatMsg {
  role: 'user' | 'assistant'
  text: string
}

type AssistantGender = 'male' | 'female'
type PanelSide = 'left' | 'right'
type PanelVertical = 'top' | 'bottom'
type DockSide = 'left' | 'right'
type AssistantRole = NonNullable<Props['roleContext']>

const ASSISTANT_META: Record<AssistantGender, { name: string; image: string; voice: string; label: string }> = {
  male: {
    name: '小慧助教',
    image: '/assets/eduhive-portal-assistant-cutout.png',
    voice: 'aisjiuxu',
    label: '男生',
  },
  female: {
    name: '小慧学姐',
    image: '/assets/eduhive-portal-assistant-female-cutout.png',
    voice: 'aisjinger',
    label: '女生',
  },
}

const STUDENT_GUIDANCE: Record<NavKey, { title: string; text: string; quick: string[]; empty: string; placeholder: string }> = {
  profile: {
    title: '学习画像',
    text: '这里汇总你的知识水平、学习节奏、呈现偏好和当前目标。你可以让我解释画像字段，或帮你判断下一步该补哪一块。',
    quick: ['我的画像说明什么？', '下一步学什么？', '怎么提升当前目标？'],
    empty: '你可以问我当前页面怎么用，也可以让我解释画像里的某个指标。',
    placeholder: '咨询画像、目标或学习建议...',
  },
  graph: {
    title: '知识图谱',
    text: '这里展示课程知识点之间的依赖关系。你可以让我解释节点、路径，或说明为什么系统这样安排学习顺序。',
    quick: ['解释当前节点', '帮我规划学习路径', '路径重点是什么？'],
    empty: '你可以问我某个知识点的作用，也可以让我解释当前路径。',
    placeholder: '咨询知识点、路径或节点含义...',
  },
  resources: {
    title: '学习资源',
    text: '这里可以查看讲义、导图、练习、案例、讲解和审核报告。你可以让我用更容易理解的方式解释资源内容。',
    quick: ['总结当前讲义', '练习题怎么做？', '给我一个学习建议'],
    empty: '你可以问我当前页面怎么用，也可以直接描述学习中卡住的地方。',
    placeholder: '打字或点麦克风提问...',
  },
  chat: {
    title: '学习对话',
    text: '这里适合提出具体学习问题和代码困惑。遇到知识难点时，我会尽量引导你梳理原因，而不是直接替你跳到答案。',
    quick: ['请引导我思考', '我哪里理解错了？', '换个例子讲讲'],
    empty: '你可以说出具体卡点，我会帮你把问题拆开。',
    placeholder: '描述你的学习问题...',
  },
  code: {
    title: '代码沙箱',
    text: '这里可以运行 Python 代码并查看输出、错误和变量快照。你可以把报错或思路发给我，我会帮你定位问题。',
    quick: ['解释这段代码', '为什么运行报错？', '给我调试步骤'],
    empty: '你可以把报错、代码片段或运行现象告诉我。',
    placeholder: '咨询代码运行、报错或调试...',
  },
  progress: {
    title: '掌握进度',
    text: '这里展示知识点掌握度、热力图和复习建议。我可以用更直白的话解释颜色、概率和薄弱点。',
    quick: ['解释掌握度', '薄弱点在哪？', '生成复习顺序'],
    empty: '你可以问我某个指标代表什么，或让系统给你复习建议。',
    placeholder: '咨询掌握度、热力图或复习安排...',
  },
}

const ROLE_GUIDANCE: Record<AssistantRole, { title: string; text: string; quick: string[]; empty: string; placeholder: string; reminderTitle: string }> = {
  student: {
    title: '课程导学',
    text: '',
    quick: [],
    empty: '',
    placeholder: '',
    reminderTitle: '学习提醒',
  },
  teacher: {
    title: '教师工作台',
    text: '这里用于创建课程、查看本人负责的课程记录，并维护课程发布状态。你可以直接把想新增的课程或想调整的状态告诉我。',
    quick: ['怎么创建课程？', '如何发布课程？', '为什么保存失败？'],
    empty: '你可以问我教师端怎么用，也可以描述课程创建、保存或发布时遇到的问题。',
    placeholder: '咨询课程创建、保存或发布...',
    reminderTitle: '工作提醒',
  },
  admin: {
    title: '管理后台',
    text: '这里用于查看用户、课程和平台统计，并维护课程状态。管理员入口不进入学生课程学习流。',
    quick: ['怎么查看用户角色？', '如何管理课程状态？', '后台数据从哪来？'],
    empty: '你可以问我管理端怎么用，也可以让我解释用户、课程或统计数据。',
    placeholder: '咨询用户、课程或系统数据...',
    reminderTitle: '管理提醒',
  },
}

const FALLBACK_TIPS: Record<AssistantRole, string[]> = {
  student: [
    '可以把当前卡住的问题直接发给我。',
    '也可以让我解释当前页面里的按钮和数据含义。',
    '如果内容太难，我可以换一种更具体的例子讲。',
  ],
  teacher: [
    '教师端目前支持课程创建、课程列表读取和课程状态维护。',
    '保存失败时，可以确认自己是否使用教师账号登录。',
    '课程资料上传后，已发布课程会在学生侧展示资料入口。',
  ],
  admin: [
    '管理端可以查看平台账号、课程和统计概览。',
    '可以查看用户角色，也可以维护课程状态。',
    '如果加载异常，先确认自己是否使用管理员账号登录。',
  ],
}

export function FloatingAssistant({ activeNav, selectedConcept, roleContext = 'student' }: Props) {
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
  const pageGuidance = STUDENT_GUIDANCE[activeNav] || STUDENT_GUIDANCE.resources
  const roleGuidance = ROLE_GUIDANCE[roleContext]
  const guidance = roleContext === 'student' ? pageGuidance : roleGuidance
  const tips = FALLBACK_TIPS[roleContext]
  const targetLabel = selectedConcept || (roleContext === 'student' ? '当前学习目标' : roleGuidance.title)
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
        setTipIndex((index) => (index + 1) % tips.length)
        setShowTip(true)
        window.setTimeout(() => setShowTip(false), 5000)
      }
    }, 60000)
    return () => clearInterval(timer)
  }, [expanded, tips.length])

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
      console.log('[EduMate digital human voice]', {
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
        const response = await assistantApi.ask(q, {
          role_context: roleContext,
          page_context: guidance.title,
          selected_concept: targetLabel,
        })
        const answer = response.data?.answer || '我已经收到你的问题，但当前没有可展示的回答。'
        setChatMessages((prev) => [...prev, { role: 'assistant', text: answer }])
      } catch {
        setChatMessages((prev) => [...prev, { role: 'assistant', text: '抱歉，数字人助理服务暂时不可用。请确认后端服务已启动。' }])
      } finally {
        setLoading(false)
      }
    },
    [guidance.title, input, loading, roleContext, targetLabel, updatePanelPlacement],
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
      aria-label="数字人助理窗口"
    >
      <header className="floating-assistant-header">
        <div className="floating-assistant-avatar">
          <img className={`is-${assistantGender}`} src={assistant.image} alt={`${assistant.label}数字人助理`} draggable={false} />
          <span className={cn(speaking && 'active')} />
        </div>
        <div className="floating-assistant-title">
          <span><Sparkles className="h-3.5 w-3.5" /> 数字人助理</span>
          <strong>{assistant.name}</strong>
          <small>{guidance.title} · {targetLabel}</small>
        </div>
        <div className="floating-assistant-window-actions">
          <button type="button" onClick={() => setFullscreen((value) => !value)} title={fullscreen ? '退出大窗口' : '放大窗口'}>
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
            <span>{guidance.empty}</span>
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
            <strong>{roleGuidance.reminderTitle}</strong>
            <span>你已经停留 {sessionMinutes} 分钟，可以回顾当前页面的下一步操作。</span>
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
            placeholder={micSupported ? guidance.placeholder : '输入你想咨询的问题...'}
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
                {tips[tipIndex]}
              </motion.div>
            )}
          </AnimatePresence>

          <AnimatePresence>
            {expanded && <div className="floating-assistant-popover">{panelContent}</div>}
          </AnimatePresence>

          <button
            type="button"
            className={cn('floating-assistant-trigger', speaking && 'is-speaking')}
            aria-label="打开数字人助理"
            onPointerDown={handleTriggerPointerDown}
            onPointerMove={handlePointerMove}
            onPointerUp={handlePointerUp}
          >
            <span className="floating-assistant-trigger-image">
              <img className={`is-${assistantGender}`} src={assistant.image} alt="" draggable={false} />
            </span>
            <span className="floating-assistant-trigger-copy">
              <strong>小慧</strong>
              <small>点我提问</small>
            </span>
          </button>
        </motion.div>
      )}
    </>
  )
}
