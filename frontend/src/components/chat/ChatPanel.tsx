/**
 * 需求：AI 学习对话面板。
 * 功能：
 *   - 与后端多智能体（Profiler/Planner/Tutor）进行 SSE 流式对话；
 *   - 根据响应类型（path_plan / code / evaluation / text）渲染不同消息卡片；
 *   - 支持快捷提示、代码一键运行到沙箱、资源生成触发。
 * 主要 props：
 *   - session：当前会话信息，用于发送聊天请求。
 * 主要 hooks/函数：
 *   - sendMessage：组装用户消息并消费 SSE 流；
 *   - parseSSE：解析 data: ... 格式的 SSE 事件；
 *   - MessageContent：按 response_type 渲染结构化内容。
 * TODO:
 *  - [已完成] 基础 SSE 流式聊天
 *  - [已完成] 路径规划/代码/评估卡片渲染
 *  - [已完成] 代码一键运行到沙箱
 *  - [已完成] 路径解释弹窗（C7）与苏格拉底提问链 UI（C8）
 *  - [待完成] 流式输出 token 级打字效果
 *  - [待完成] 消息历史持久化与滚动定位优化
 *  - [待完成] 多轮对话上下文折叠与摘要
 */
import { useEffect, useRef, useState } from 'react'
import { AnimatePresence, motion } from 'framer-motion'
import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'
import rehypeHighlight from 'rehype-highlight'
import {
  Send,
  Bot,
  User,
  Sparkles,
  Play,
  CheckCircle,
  Lightbulb,
} from 'lucide-react'

import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { GlassCard } from '@/components/ui/glass-card'
import { IconBox } from '@/components/ui/icon-box'
import { PathExplanation } from '@/components/learning-path/PathExplanation'
import { SocraticPanel } from '@/components/socratic/SocraticPanel'
import { sessionApi, type AgentResponse, type SessionResponse } from '@/services/api'
import { useSandboxStore } from '@/stores/sandboxStore'
import { cn } from '@/lib/utils'

interface Props {
  session: SessionResponse
}

interface Message {
  role: 'user' | 'assistant' | 'system'
  content: string
  agentName?: string
  isStreaming?: boolean
  data?: AgentResponse
}

const QUICK_PROMPTS = [
  '我想学习 Python 变量与赋值',
  '帮我规划 Python 学习路径',
  '出一道循环结构的练习题',
]

// 解析 SSE data: {...} 行，失败或非 data 行返回 null
function parseSSE(line: string): any | null {
  if (!line.startsWith('data: ')) return null
  try {
    return JSON.parse(line.slice(6))
  } catch {
    return null
  }
}

export function ChatPanel({ session }: Props) {
  const [input, setInput] = useState('')
  const [messages, setMessages] = useState<Message[]>([
    {
      role: 'assistant',
      content:
        '你好！我是智慧伴学学习助手。告诉我你想学习哪个 Python 知识点，或者让我为你规划一条学习路径。',
      agentName: 'Profiler',
    },
  ])
  const [loading, setLoading] = useState(false)
  const bottomRef = useRef<HTMLDivElement>(null)
  const textareaRef = useRef<HTMLTextAreaElement>(null)
  const setSandboxCode = useSandboxStore((s) => s.setCode)

  // 消息列表变化时自动滚动到底部
  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  // 根据输入内容自适应调整 textarea 高度，最大 160px
  const adjustTextareaHeight = () => {
    const el = textareaRef.current
    if (!el) return
    el.style.height = 'auto'
    el.style.height = `${Math.min(el.scrollHeight, 160)}px`
  }

  // 发送用户消息，消费 SSE 流并实时更新最后一条 assistant 占位消息
  const sendMessage = async (text?: string) => {
    const messageText = text ?? input
    if (!messageText.trim()) return

    setInput('')
    if (textareaRef.current) textareaRef.current.style.height = 'auto'

    setMessages((prev) => [...prev, { role: 'user', content: messageText.trim() }])
    setLoading(true)

    setMessages((prev) => [
      ...prev,
      { role: 'assistant', content: '', agentName: '...', isStreaming: true },
    ])

    try {
      const response = await sessionApi.chatStream(session.session_id, messageText.trim())
      const reader = response.body?.getReader()
      if (!reader) throw new Error('无法建立流式连接')

      const decoder = new TextDecoder()
      let buffer = ''
      let finalResponse: AgentResponse | null = null

      while (true) {
        const { done, value } = await reader.read()
        if (done) break

        buffer += decoder.decode(value, { stream: true })
        const lines = buffer.split('\n')
        buffer = lines.pop() || ''

        for (const line of lines) {
          const event = parseSSE(line.trim())
          if (!event) continue

          // 流式中：更新占位消息的思考状态与代理名称
          if (event.type === 'thinking' || event.type === 'progress') {
            setMessages((prev) => {
              const last = prev[prev.length - 1]
              if (last?.role === 'assistant' && last.isStreaming) {
                return [
                  ...prev.slice(0, -1),
                  {
                    ...last,
                    agentName: event.agent || 'Agent',
                    content: event.message || last.content,
                  },
                ]
              }
              return prev
            })
          // 流式结束：用最终 AgentResponse 替换占位消息
          } else if (event.type === 'complete') {
            finalResponse = event.agent_response as AgentResponse
            setMessages((prev) => {
              const last = prev[prev.length - 1]
              if (last?.role === 'assistant' && last.isStreaming) {
                return [
                  ...prev.slice(0, -1),
                  {
                    role: 'assistant',
                    content: finalResponse?.content?.message || JSON.stringify(finalResponse?.content),
                    agentName: finalResponse?.agent_name || 'Agent',
                    isStreaming: false,
                    data: finalResponse ?? undefined,
                  },
                ]
              }
              return prev
            })
          // 后端返回错误事件，移除占位消息并展示系统提示
          } else if (event.type === 'error') {
            setMessages((prev) => [
              ...prev.slice(0, -1),
              { role: 'system', content: `流式输出出错：${event.message}` },
            ])
          }
        }
      }

      if (!finalResponse) {
        setMessages((prev) => {
          const last = prev[prev.length - 1]
          if (last?.role === 'assistant' && last.isStreaming) {
            return [
              ...prev.slice(0, -1),
              { role: 'assistant', content: '（流式响应已结束，但未收到完整结果）', agentName: 'System' },
            ]
          }
          return prev
        })
      }
    } catch (err: any) {
      setMessages((prev) => [
        ...prev.slice(0, -1),
        { role: 'system', content: `抱歉，服务暂时异常：${err.message || '请稍后重试'}` },
      ])
    } finally {
      setLoading(false)
    }
  }

  // Enter 发送，Shift + Enter 换行
  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      sendMessage()
    }
  }

  // 触发 ResourceViewer 生成指定知识点资源
  const triggerGenerateResource = (concept: string) => {
    window.dispatchEvent(new CustomEvent('eduhive:generate-resource', { detail: { concept } }))
  }

  // 继续苏格拉底引导时发送下一条消息
  const continueSocratic = () => {
    sendMessage('请继续引导我')
  }

  // 将代码写入沙箱 store 并切换至沙箱标签
  const openSandboxWithCode = (code: string) => {
    setSandboxCode(code)
    window.dispatchEvent(new CustomEvent('eduhive:open-sandbox'))
  }

  // 取最后一条非流式的助手消息，用于判断是否展示快捷提示
  const lastAssistant = messages.filter((m) => m.role === 'assistant' && !m.isStreaming).pop()

  return (
    <GlassCard className="flex h-[calc(100vh-12rem)] min-h-[520px] flex-col overflow-hidden" hover={false}>
      {/* Header */}
      <div className="flex items-center justify-between border-b border-slate-100 bg-gradient-to-r from-indigo-50/50 to-violet-50/50 px-5 py-4">
        <div className="flex items-center gap-3">
          <IconBox icon={Sparkles} variant="indigo" size="sm" />
          <div>
            <h3 className="text-base font-bold text-slate-900">AI 学习对话</h3>
            <p className="text-xs text-slate-500">多智能体实时协作辅导</p>
          </div>
        </div>
        <div className="hidden items-center gap-2 sm:flex">
          {['Profiler', 'Planner', 'Tutor'].map((agent) => (
            <Badge
              key={agent}
              variant="secondary"
              className="border-0 bg-white/70 text-xs font-medium text-slate-600 backdrop-blur-sm"
            >
              {agent}
            </Badge>
          ))}
        </div>
      </div>

      {/* Messages */}
      <div className="flex-1 overflow-y-auto px-5 py-5">
        <div className="space-y-5">
          <AnimatePresence initial={false}>
            {messages.map((msg, idx) => (
              <MessageBubble
                key={idx}
                msg={msg}
                index={idx}
                onRunCode={openSandboxWithCode}
                onGenerateResource={triggerGenerateResource}
                onContinueSocratic={continueSocratic}
              />
            ))}
          </AnimatePresence>
          <div ref={bottomRef} />
        </div>
      </div>

      {/* Quick prompts */}
      <AnimatePresence>
        {lastAssistant && !loading && (
          <motion.div
            initial={{ opacity: 0, y: 8 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: 4 }}
            className="flex flex-wrap gap-2 border-t border-slate-100 bg-slate-50/50 px-5 py-3"
          >
            {QUICK_PROMPTS.map((prompt) => (
              <button
                key={prompt}
                onClick={() => sendMessage(prompt)}
                className="inline-flex items-center gap-1.5 rounded-full border border-slate-200 bg-white px-3 py-1.5 text-xs font-semibold text-slate-600 shadow-sm transition-all hover:-translate-y-0.5 hover:border-indigo-200 hover:bg-indigo-50 hover:text-indigo-700 hover:shadow-md"
              >
                <Lightbulb className="h-3 w-3" />
                {prompt}
              </button>
            ))}
          </motion.div>
        )}
      </AnimatePresence>

      {/* Input */}
      <div className="border-t border-slate-100 p-4">
        <div className="flex gap-2 rounded-2xl border border-slate-200 bg-white/80 p-2 shadow-sm backdrop-blur-sm transition-all focus-within:border-indigo-300 focus-within:ring-2 focus-within:ring-indigo-500/20 focus-within:shadow-md">
          <textarea
            ref={textareaRef}
            value={input}
            onChange={(e) => {
              setInput(e.target.value)
              adjustTextareaHeight()
            }}
            onKeyDown={handleKeyDown}
            disabled={loading}
            rows={1}
            placeholder="输入你想学习的 Python 知识点，按 Enter 发送，Shift + Enter 换行..."
            className="max-h-40 min-h-[44px] flex-1 resize-none bg-transparent px-3 py-2.5 text-sm outline-none placeholder:text-slate-400"
          />
          <Button
            onClick={() => sendMessage()}
            disabled={loading || !input.trim()}
            className="h-auto rounded-xl bg-gradient-to-r from-indigo-600 to-violet-600 px-4 shadow-lg shadow-indigo-500/25 transition-transform active:scale-95 disabled:opacity-60"
          >
            <Send className="h-4 w-4" />
          </Button>
        </div>
      </div>
    </GlassCard>
  )
}

function MessageBubble({
  msg,
  index,
  onRunCode,
  onGenerateResource,
  onContinueSocratic,
}: {
  msg: Message
  index: number
  onRunCode: (code: string) => void
  onGenerateResource: (concept: string) => void
  onContinueSocratic?: () => void
}) {
  const isUser = msg.role === 'user'
  const isSystem = msg.role === 'system'

  return (
    <motion.div
      initial={{ opacity: 0, y: 16, scale: 0.98 }}
      animate={{ opacity: 1, y: 0, scale: 1 }}
      transition={{ duration: 0.35, delay: index * 0.03, ease: [0.16, 1, 0.3, 1] }}
      className={cn('flex gap-3', isUser ? 'justify-end' : 'justify-start')}
    >
      {!isUser && (
        <div className="shrink-0 pt-1">
          {isSystem ? (
            <IconBox icon={Sparkles} variant="amber" size="sm" />
          ) : (
            <IconBox icon={Bot} variant="indigo" size="sm" />
          )}
        </div>
      )}

      <div
        className={cn(
          'max-w-[85%] rounded-2xl px-4 py-3 text-sm shadow-sm sm:max-w-[75%]',
          isUser
            ? 'rounded-tr-sm bg-gradient-to-br from-indigo-600 to-violet-700 text-white'
            : isSystem
            ? 'rounded-tl-sm border border-amber-200/80 bg-amber-50/90 text-amber-900'
            : 'rounded-tl-sm border border-slate-200/80 bg-white/90 text-slate-800'
        )}
      >
        {!isUser && !isSystem && (
          <div className="mb-1.5 flex items-center gap-2 text-xs text-slate-500">
            <Bot className="h-3.5 w-3.5" />
            <span className="font-semibold">{msg.agentName || 'Assistant'}</span>
          </div>
        )}
        {isUser && (
          <div className="mb-1.5 flex items-center justify-end gap-1.5 text-xs text-white/80">
            <span className="font-semibold">你</span>
            <User className="h-3.5 w-3.5" />
          </div>
        )}

        <MessageContent
          msg={msg}
          onRunCode={onRunCode}
          onGenerateResource={onGenerateResource}
          onContinueSocratic={onContinueSocratic}
        />
      </div>

      {isUser && (
        <div className="shrink-0 pt-1">
          <IconBox icon={User} variant="violet" size="sm" />
        </div>
      )}
    </motion.div>
  )
}

function MessageContent({
  msg,
  onRunCode,
  onGenerateResource,
  onContinueSocratic,
}: {
  msg: Message
  onRunCode: (code: string) => void
  onGenerateResource: (concept: string) => void
  onContinueSocratic?: () => void
}) {
  if (msg.isStreaming && !msg.content) {
    return (
      <div className="flex items-center gap-2 text-slate-500">
        <span className="typing-dot" />
        <span className="typing-dot" />
        <span className="typing-dot" />
        <span className="ml-1 text-xs">正在思考...</span>
      </div>
    )
  }

  const data = msg.data
  const responseType = data?.response_type

  // 路径规划：展示推荐路径、预计时长与资源生成入口
  if (
    (responseType === 'path_plan' || responseType === 'navigator') &&
    typeof data?.content === 'object'
  ) {
    const content = data.content as {
      message?: string
      target_concept?: string
      suggested_path?: string[]
      path?: string[]
      path_explanation?: string[]
      estimated_minutes?: number
      next_action?: string
    }
    const path = content.suggested_path || content.path || []
    return (
      <div className="space-y-3">
        <div className="prose prose-sm max-w-none text-slate-700">
          <ReactMarkdown remarkPlugins={[remarkGfm]} rehypePlugins={[rehypeHighlight]}>
            {content.message || msg.content}
          </ReactMarkdown>
        </div>
        {path.length > 0 && (
          <PathExplanation
            path={path}
            explanations={content.path_explanation}
            estimatedMinutes={content.estimated_minutes}
            onGenerate={onGenerateResource}
          />
        )}
        {content.target_concept && content.next_action === 'generate_resource' && (
          <Button
            size="sm"
            className="gap-1.5 rounded-xl bg-gradient-to-r from-indigo-600 to-violet-600 shadow-lg shadow-indigo-500/25 transition-transform hover:scale-[1.02] active:scale-95"
            onClick={() => onGenerateResource(content.target_concept!)}
          >
            <Sparkles className="h-3.5 w-3.5" />
            生成「{content.target_concept}」学习资源
          </Button>
        )}
      </div>
    )
  }

  // 学习资源最终响应（Reviewer 返回）：展示路径解释与资源生成入口
  if (responseType === 'reviewer' && typeof data?.content === 'object') {
    const content = data.content as {
      message?: string
      concept?: string
      path?: string[]
      path_explanation?: string[]
      estimated_minutes?: number
      package?: any
    }
    const path = content.path || []
    return (
      <div className="space-y-3">
        <div className="prose prose-sm max-w-none text-slate-700">
          <ReactMarkdown remarkPlugins={[remarkGfm]} rehypePlugins={[rehypeHighlight]}>
            {content.message || msg.content}
          </ReactMarkdown>
        </div>
        {path.length > 0 && (
          <PathExplanation
            path={path}
            explanations={content.path_explanation}
            estimatedMinutes={content.estimated_minutes}
            onGenerate={onGenerateResource}
          />
        )}
        {content.concept && (
          <Button
            size="sm"
            className="gap-1.5 rounded-xl bg-gradient-to-r from-indigo-600 to-violet-600 shadow-lg shadow-indigo-500/25 transition-transform hover:scale-[1.02] active:scale-95"
            onClick={() => onGenerateResource(content.concept!)}
          >
            <Sparkles className="h-3.5 w-3.5" />
            查看「{content.concept}」学习资源
          </Button>
        )}
      </div>
    )
  }

  // 苏格拉底辅导：展示引导问题、提示与答案
  if (responseType === 'tutor' && typeof data?.content === 'object') {
    const content = data.content as {
      question?: string
      hint?: string
      answer?: string
      can_provide_answer?: boolean
      stage?: string
    }
    return (
      <SocraticPanel
        question={content.question || msg.content}
        hint={content.hint}
        answer={content.answer}
        canProvideAnswer={content.can_provide_answer}
        stage={content.stage}
        onNext={onContinueSocratic}
      />
    )
  }

  // 代码响应：渲染说明与可一键运行的代码块
  if (responseType === 'code' && typeof data?.content === 'object') {
    const content = data.content as { code?: string; message?: string }
    return (
      <div className="space-y-2">
        <div className="prose prose-sm max-w-none text-slate-700">
          <ReactMarkdown remarkPlugins={[remarkGfm]} rehypePlugins={[rehypeHighlight]}>
            {content.message || msg.content}
          </ReactMarkdown>
        </div>
        {content.code && (
          <div className="group relative overflow-hidden rounded-xl bg-slate-950 shadow-inner">
            <div className="flex items-center justify-between border-b border-slate-800 px-3 py-2">
              <div className="flex items-center gap-1.5">
                <span className="h-2.5 w-2.5 rounded-full bg-red-500" />
                <span className="h-2.5 w-2.5 rounded-full bg-amber-500" />
                <span className="h-2.5 w-2.5 rounded-full bg-emerald-500" />
              </div>
              <Button
                size="sm"
                variant="ghost"
                className="h-7 gap-1 text-xs text-slate-300 hover:bg-slate-800 hover:text-white"
                onClick={() => onRunCode(content.code!)}
              >
                <Play className="h-3 w-3" />
                运行
              </Button>
            </div>
            <pre className="overflow-x-auto p-3 text-xs">
              <code className="font-mono text-slate-50">{content.code}</code>
            </pre>
          </div>
        )}
      </div>
    )
  }

  // 评估响应：展示评分与学习建议
  if (responseType === 'evaluation' && typeof data?.content === 'object') {
    const content = data.content as {
      summary?: string
      score?: number
      recommendations?: string[]
    }
    return (
      <div className="space-y-2">
        <div className="flex items-center gap-2 text-emerald-600">
          <CheckCircle className="h-4 w-4" />
          <span className="font-bold">学习评估</span>
          {typeof content.score === 'number' && (
            <Badge variant="outline" className="border-emerald-200 text-emerald-700">
              {content.score.toFixed(1)} 分
            </Badge>
          )}
        </div>
        <div className="prose prose-sm max-w-none text-slate-700">
          <ReactMarkdown remarkPlugins={[remarkGfm]} rehypePlugins={[rehypeHighlight]}>
            {content.summary || msg.content}
          </ReactMarkdown>
        </div>
        {content.recommendations && content.recommendations.length > 0 && (
          <ul className="list-disc space-y-1 rounded-xl border border-emerald-100 bg-emerald-50/50 p-3 pl-5 text-xs text-slate-600">
            {content.recommendations.map((r, i) => (
              <li key={i}>{r}</li>
            ))}
          </ul>
        )}
      </div>
    )
  }

  return (
    <div className="prose prose-sm max-w-none text-slate-700">
      <ReactMarkdown remarkPlugins={[remarkGfm]} rehypePlugins={[rehypeHighlight]}>
        {msg.content}
      </ReactMarkdown>
    </div>
  )
}
