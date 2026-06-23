import { Send, Bot, User, Sparkles, MapPin, Clock, ArrowRight, Play, CheckCircle } from 'lucide-react'
import { useEffect, useRef, useState } from 'react'

import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Input } from '@/components/ui/input'
import { sessionApi, type AgentResponse, type SessionResponse } from '@/services/api'
import { useSandboxStore } from '@/stores/sandboxStore'

/**
 * TODO:
 * - [已完成] 支持 Markdown 渲染助手消息
 * - [已完成] 实现流式输出效果（SSE）
 * - [已完成] 显示 Agent 名称与头像
 * - [待完成] 根据 response_type 显示不同 UI（路径规划、资源卡片、辅导提问等）
 * - [待完成] 支持代码消息类型与一键运行
 */

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
      content: '你好！我是智学蜂巢学习助手。告诉我你想学习哪个 Python 知识点？',
      agentName: 'Profiler',
    },
  ])
  const [loading, setLoading] = useState(false)
  const bottomRef = useRef<HTMLDivElement>(null)
  const setSandboxCode = useSandboxStore((s) => s.setCode)

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  const sendMessage = async () => {
    if (!input.trim()) return

    const userMsg = input.trim()
    setInput('')
    setMessages((prev) => [...prev, { role: 'user', content: userMsg }])
    setLoading(true)

    // 先放置一个正在思考的占位消息
    setMessages((prev) => [
      ...prev,
      { role: 'assistant', content: '', agentName: '...', isStreaming: true },
    ])

    try {
      const response = await sessionApi.chatStream(session.session_id, userMsg)
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
          } else if (event.type === 'error') {
            setMessages((prev) => [
              ...prev.slice(0, -1),
              { role: 'system', content: `流式输出出错：${event.message}` },
            ])
          }
        }
      }

      // 如果流结束但没有收到 complete，fallback 显示最后内容
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

  const triggerGenerateResource = (concept: string) => {
    window.dispatchEvent(
      new CustomEvent('eduhive:generate-resource', { detail: { concept } })
    )
  }

  const openSandboxWithCode = (code: string) => {
    setSandboxCode(code)
    window.dispatchEvent(new CustomEvent('eduhive:open-sandbox'))
  }

  const renderAssistantContent = (msg: Message) => {
    if (msg.isStreaming && !msg.content) {
      return <span className="animate-pulse">正在思考...</span>
    }

    const data = msg.data
    const responseType = data?.response_type

    if (responseType === 'path_plan' && typeof data?.content === 'object') {
      const content = data.content as {
        message?: string
        target_concept?: string
        suggested_path?: string[]
        estimated_minutes?: number
        next_action?: string
      }
      const path = content.suggested_path || []
      return (
        <div className="space-y-3">
          <p className="whitespace-pre-wrap">{content.message || msg.content}</p>
          {path.length > 0 && (
            <div className="bg-background/60 rounded-lg p-3 space-y-2">
              <div className="flex items-center gap-2 text-xs font-medium text-muted-foreground">
                <MapPin className="w-3.5 h-3.5" />
                推荐学习路径
              </div>
              <div className="flex flex-wrap items-center gap-2">
                {path.map((step, i) => (
                  <span key={i} className="flex items-center gap-2">
                    <Badge variant="secondary" className="text-xs">{step}</Badge>
                    {i < path.length - 1 && <ArrowRight className="w-3 h-3 text-muted-foreground" />}
                  </span>
                ))}
              </div>
              {content.estimated_minutes && (
                <div className="flex items-center gap-1 text-xs text-muted-foreground">
                  <Clock className="w-3 h-3" />
                  预计 {content.estimated_minutes} 分钟
                </div>
              )}
            </div>
          )}
          {content.target_concept && content.next_action === 'generate_resource' && (
            <Button
              size="sm"
              className="gap-1.5"
              onClick={() => triggerGenerateResource(content.target_concept!)}
            >
              <Sparkles className="w-3.5 h-3.5" />
              生成「{content.target_concept}」学习资源
            </Button>
          )}
        </div>
      )
    }

    if (responseType === 'code' && typeof data?.content === 'object') {
      const content = data.content as { code?: string; message?: string }
      return (
        <div className="space-y-2">
          <p className="whitespace-pre-wrap">{content.message || msg.content}</p>
          {content.code && (
            <div className="relative group">
              <pre className="bg-slate-950 text-slate-50 p-3 rounded-lg text-xs overflow-x-auto">
                <code>{content.code}</code>
              </pre>
              <Button
                size="sm"
                variant="secondary"
                className="absolute top-2 right-2 opacity-0 group-hover:opacity-100 transition-opacity gap-1"
                onClick={() => openSandboxWithCode(content.code!)}
              >
                <Play className="w-3 h-3" />
                运行
              </Button>
            </div>
          )}
        </div>
      )
    }

    if (responseType === 'evaluation' && typeof data?.content === 'object') {
      const content = data.content as { summary?: string; score?: number; recommendations?: string[] }
      return (
        <div className="space-y-2">
          <div className="flex items-center gap-2 text-green-600">
            <CheckCircle className="w-4 h-4" />
            <span className="font-medium">学习评估</span>
            {typeof content.score === 'number' && <Badge variant="outline">{content.score.toFixed(1)} 分</Badge>}
          </div>
          <p className="whitespace-pre-wrap">{content.summary || msg.content}</p>
          {content.recommendations && content.recommendations.length > 0 && (
            <ul className="list-disc list-inside text-xs text-muted-foreground">
              {content.recommendations.map((r, i) => <li key={i}>{r}</li>)}
            </ul>
          )}
        </div>
      )
    }

    return <div className="whitespace-pre-wrap">{msg.content}</div>
  }

  return (
    <Card className="h-[600px] flex flex-col">
      <CardHeader className="pb-3">
        <CardTitle className="text-lg flex items-center gap-2">
          <Sparkles className="w-5 h-5 text-blue-500" />
          学习对话
        </CardTitle>
      </CardHeader>
      <CardContent className="flex-1 flex flex-col">
        <div className="flex-1 overflow-y-auto space-y-4 pr-2">
          {messages.map((msg, idx) => (
            <div key={idx} className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}>
              <div
                className={`max-w-[90%] rounded-2xl px-4 py-3 text-sm ${
                  msg.role === 'user'
                    ? 'bg-primary text-primary-foreground'
                    : msg.role === 'system'
                    ? 'bg-red-50 text-red-700 dark:bg-red-950 dark:text-red-300'
                    : 'bg-muted'
                }`}
              >
                {msg.role === 'assistant' && (
                  <div className="flex items-center gap-1.5 mb-1.5 text-xs text-muted-foreground">
                    <Bot className="w-3.5 h-3.5" />
                    <span className="font-medium">{msg.agentName || 'Assistant'}</span>
                  </div>
                )}
                {msg.role === 'user' && (
                  <div className="flex items-center justify-end gap-1.5 mb-1.5 text-xs text-primary-foreground/80">
                    <span className="font-medium">你</span>
                    <User className="w-3.5 h-3.5" />
                  </div>
                )}
                {renderAssistantContent(msg)}
              </div>
            </div>
          ))}
          <div ref={bottomRef} />
        </div>
        <div className="flex gap-2 mt-4">
          <Input
            placeholder="输入你想学习的 Python 知识点..."
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={(e) => e.key === 'Enter' && sendMessage()}
            disabled={loading}
          />
          <Button onClick={sendMessage} disabled={loading}>
            <Send className="w-4 h-4" />
          </Button>
        </div>
      </CardContent>
    </Card>
  )
}
