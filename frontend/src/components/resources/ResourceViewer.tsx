import { useEffect, useRef, useState } from 'react'
import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'
import rehypeHighlight from 'rehype-highlight'
import {
  BookOpen,
  CheckCircle,
  AlertCircle,
  XCircle,
  Lightbulb,
  Play,
  Code2,
  FileText,
  Map,
  ListChecks,
  Loader2,
} from 'lucide-react'

import { Button } from '@/components/ui/button'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { Progress } from '@/components/ui/progress'
import api, { resourceApi } from '@/services/api'
import { useSandboxStore } from '@/stores/sandboxStore'

/**
 * TODO:
 * - [已完成] 使用 Markdown 渲染讲解文档
 * - [已完成] 使用 Mermaid 渲染思维导图
 * - [已完成] 显示完整的辩论议会报告
 * - [已完成] 练习题交互与一键运行到 Pyodide 沙箱
 * - [已完成] 接入 SSE 流式生成并显示进度
 * - [已完成] 练习题后端自动判题
 * - [待完成] 根据认知风格渲染不同形态（视觉/听觉/动觉）
 * - [待完成] TTS 语音播放
 */

interface Props {
  sessionId?: string
}

interface DebateRound {
  round: number
  agent: string
  verdict: 'PASS' | 'WARN' | 'REJECT' | 'VETO'
  message: string
  suggestion?: string
}

interface Exercise {
  question: string
  starter_code?: string
  expected_output?: string
  hints?: string[]
  solution?: string
}

interface CodeCase {
  title: string
  code: string
  explanation?: string
}

interface ResourcePackage {
  concept: string
  document: string
  mindmap: string
  exercises: Exercise[]
  code_cases: CodeCase[]
  audio_text: string
}

interface DebateReport {
  status: 'PASSED' | 'MODIFIED' | 'REJECTED'
  rounds: DebateRound[]
  final_votes: Record<string, string>
}

interface ResourceResult {
  concept: string
  package: ResourcePackage
  debate_report: DebateReport
  validation: {
    forbidden_concepts: string[]
    ast_violations: string[]
  }
}

const STAGE_PROGRESS: Record<string, number> = {
  builder: 20,
  validation: 60,
  debate: 85,
  complete: 100,
}

function parseSSE(line: string): any | null {
  if (!line.startsWith('data: ')) return null
  try {
    return JSON.parse(line.slice(6))
  } catch {
    return null
  }
}

export function ResourceViewer({ sessionId }: Props) {
  const [concept, setConcept] = useState('变量与赋值')
  const [resource, setResource] = useState<ResourceResult | null>(null)
  const [loading, setLoading] = useState(false)
  const [progressMessage, setProgressMessage] = useState('')
  const [progressValue, setProgressValue] = useState(0)
  const mindmapRef = useRef<HTMLDivElement>(null)
  const setSandboxCode = useSandboxStore((s) => s.setCode)

  // 练习题判题状态
  const [judgeResults, setJudgeResults] = useState<Record<number, { loading: boolean; result?: any }>>({})
  const [exerciseCodes, setExerciseCodes] = useState<Record<number, string>>({})

  const generate = async (targetConcept?: string) => {
    if (!sessionId) {
      alert('会话尚未初始化，请稍后再试')
      return
    }

    const conceptToGenerate = targetConcept || concept
    if (targetConcept) {
      setConcept(targetConcept)
    }

    setLoading(true)
    setProgressValue(5)
    setProgressMessage('准备生成资源...')
    setResource(null)

    try {
      const response = await resourceApi.generateStream(sessionId, conceptToGenerate)
      const reader = response.body?.getReader()
      if (!reader) throw new Error('无法建立流式连接')

      const decoder = new TextDecoder()
      let buffer = ''
      let finalResource: ResourceResult | null = null

      while (true) {
        const { done, value } = await reader.read()
        if (done) break

        buffer += decoder.decode(value, { stream: true })
        const lines = buffer.split('\n')
        buffer = lines.pop() || ''

        for (const line of lines) {
          const event = parseSSE(line.trim())
          if (!event) continue

          if (event.type === 'progress') {
            setProgressMessage(event.message || '')
            setProgressValue(STAGE_PROGRESS[event.stage] || 50)
          } else if (event.type === 'complete') {
            finalResource = event as ResourceResult
            setResource(finalResource)
            setProgressValue(100)
          } else if (event.type === 'error') {
            throw new Error(event.message || '生成失败')
          }
        }
      }

      if (!finalResource) {
        // fallback 到同步接口
        const res = await api.post('/resources/generate-for-session/default', null, { params: { concept: conceptToGenerate } })
        setResource(res.data as ResourceResult)
        setProgressValue(100)
      }
    } catch (err: any) {
      setProgressMessage(`生成失败：${err.message || '未知错误'}`)
      setProgressValue(0)
    } finally {
      setLoading(false)
    }
  }

  // 监听对话面板触发的资源生成事件
  useEffect(() => {
    const handler = (e: Event) => {
      const detail = (e as CustomEvent).detail as { concept?: string } | undefined
      if (detail?.concept) {
        generate(detail.concept)
      }
    }
    window.addEventListener('eduhive:generate-resource', handler)
    return () => window.removeEventListener('eduhive:generate-resource', handler)
  }, [sessionId])

  useEffect(() => {
    if (!mindmapRef.current || !resource?.package.mindmap) return

    const render = async () => {
      try {
        const mermaid = (await import('mermaid')).default
        mermaid.initialize({ startOnLoad: false, theme: 'default' })
        const id = `mermaid-${Math.random().toString(36).slice(2)}`
        const { svg } = await mermaid.render(id, resource.package.mindmap)
        mindmapRef.current!.innerHTML = svg
      } catch (err) {
        mindmapRef.current!.innerHTML = `<pre class="text-xs text-red-500">${String(err)}</pre>`
      }
    }
    render()
  }, [resource?.package.mindmap])

  const runInSandbox = (code: string) => {
    setSandboxCode(code)
    window.dispatchEvent(new CustomEvent('eduhive:open-sandbox'))
  }

  const runJudge = async (idx: number, exercise: Exercise) => {
    const code = exerciseCodes[idx] ?? exercise.starter_code ?? ''
    if (!code) return

    setJudgeResults((prev) => ({ ...prev, [idx]: { loading: true } }))
    try {
      const res = await api.post('/code/judge', {
        code,
        expected_output: exercise.expected_output || '',
      })
      setJudgeResults((prev) => ({ ...prev, [idx]: { loading: false, result: res.data } }))
    } catch (err: any) {
      setJudgeResults((prev) => ({
        ...prev,
        [idx]: { loading: false, result: { passed: false, reason: err.message || '判题请求失败' } },
      }))
    }
  }

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'PASSED':
        return <CheckCircle className="w-4 h-4 text-green-500" />
      case 'MODIFIED':
        return <AlertCircle className="w-4 h-4 text-yellow-500" />
      case 'REJECTED':
        return <XCircle className="w-4 h-4 text-red-500" />
      default:
        return null
    }
  }

  const getVerdictColor = (verdict: string) => {
    switch (verdict) {
      case 'PASS':
        return 'bg-green-100 text-green-700 dark:bg-green-900 dark:text-green-300'
      case 'WARN':
        return 'bg-yellow-100 text-yellow-700 dark:bg-yellow-900 dark:text-yellow-300'
      case 'REJECT':
      case 'VETO':
        return 'bg-red-100 text-red-700 dark:bg-red-900 dark:text-red-300'
      default:
        return 'bg-gray-100 text-gray-700'
    }
  }

  return (
    <div className="space-y-4">
      <div className="flex gap-2">
        <input
          className="flex-1 h-10 rounded-md border border-input bg-background px-3 py-2 text-sm"
          value={concept}
          onChange={(e) => setConcept(e.target.value)}
          placeholder="输入知识点"
        />
        <Button onClick={() => generate()} disabled={loading} size="sm">
          {loading ? <Loader2 className="w-4 h-4 animate-spin" /> : '生成'}
        </Button>
      </div>

      {loading && (
        <div className="space-y-2">
          <div className="flex justify-between text-xs text-muted-foreground">
            <span>{progressMessage || '生成中...'}</span>
            <span>{progressValue}%</span>
          </div>
          <Progress value={progressValue} className="h-2" />
        </div>
      )}

      {resource && (
        <Tabs defaultValue="document" className="w-full">
          <TabsList className="grid w-full grid-cols-4">
            <TabsTrigger value="document">
              <FileText className="w-3 h-3 mr-1" /> 文档
            </TabsTrigger>
            <TabsTrigger value="mindmap">
              <Map className="w-3 h-3 mr-1" /> 导图
            </TabsTrigger>
            <TabsTrigger value="exercises">
              <ListChecks className="w-3 h-3 mr-1" /> 练习
            </TabsTrigger>
            <TabsTrigger value="debate">
              <BookOpen className="w-3 h-3 mr-1" /> 审核
            </TabsTrigger>
          </TabsList>

          <TabsContent value="document" className="mt-2">
            <Card>
              <CardContent className="pt-4">
                <article className="prose prose-sm dark:prose-invert max-w-none">
                  <ReactMarkdown remarkPlugins={[remarkGfm]} rehypePlugins={[rehypeHighlight]}>
                    {resource.package.document}
                  </ReactMarkdown>
                </article>
              </CardContent>
            </Card>
          </TabsContent>

          <TabsContent value="mindmap" className="mt-2">
            <Card>
              <CardContent className="pt-4">
                <div ref={mindmapRef} className="flex justify-center overflow-auto" />
              </CardContent>
            </Card>
          </TabsContent>

          <TabsContent value="exercises" className="mt-2 space-y-3">
            {resource.package.code_cases?.length > 0 && (
              <Card>
                <CardHeader className="pb-2">
                  <CardTitle className="text-sm flex items-center gap-2">
                    <Code2 className="w-4 h-4 text-blue-500" />
                    实操案例
                  </CardTitle>
                </CardHeader>
                <CardContent className="space-y-3">
                  {resource.package.code_cases.map((c, i) => (
                    <div key={i} className="rounded-lg border p-3">
                      <div className="font-medium text-sm mb-2">{c.title}</div>
                      <pre className="text-xs bg-slate-950 text-slate-50 p-3 rounded-lg overflow-auto">
                        <code>{c.code}</code>
                      </pre>
                      {c.explanation && (
                        <p className="text-xs text-muted-foreground mt-2">{c.explanation}</p>
                      )}
                      <Button
                        variant="outline"
                        size="sm"
                        className="mt-2"
                        onClick={() => runInSandbox(c.code)}
                      >
                        <Play className="w-3 h-3 mr-1" /> 在沙箱运行
                      </Button>
                    </div>
                  ))}
                </CardContent>
              </Card>
            )}

            {resource.package.exercises?.map((ex, i) => (
              <Card key={i}>
                <CardHeader className="pb-2">
                  <CardTitle className="text-sm flex items-center gap-2">
                    <ListChecks className="w-4 h-4 text-green-500" />
                    练习 {i + 1}
                  </CardTitle>
                </CardHeader>
                <CardContent className="space-y-3">
                  <p className="text-sm">{ex.question}</p>
                  {ex.starter_code && (
                    <textarea
                      className="w-full h-32 font-mono text-xs p-3 rounded-lg border bg-slate-950 text-slate-50 resize-none focus:outline-none focus:ring-2 focus:ring-ring"
                      defaultValue={ex.starter_code}
                      onChange={(e) =>
                        setExerciseCodes((prev) => ({ ...prev, [i]: e.target.value }))
                      }
                    />
                  )}
                  {ex.hints && ex.hints.length > 0 && (
                    <div className="text-xs text-muted-foreground">
                      <Lightbulb className="w-3 h-3 inline mr-1" />
                      提示：{ex.hints.join('；')}
                    </div>
                  )}
                  {ex.expected_output && (
                    <div className="text-xs text-muted-foreground">
                      期望输出：<code className="bg-muted px-1 rounded">{ex.expected_output}</code>
                    </div>
                  )}
                  <div className="flex gap-2">
                    {ex.starter_code && (
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={() => runInSandbox(exerciseCodes[i] ?? ex.starter_code)}
                      >
                        <Play className="w-3 h-3 mr-1" /> 在沙箱运行
                      </Button>
                    )}
                    {ex.expected_output && (
                      <Button
                        size="sm"
                        onClick={() => runJudge(i, ex)}
                        disabled={judgeResults[i]?.loading}
                      >
                        {judgeResults[i]?.loading ? (
                          <Loader2 className="w-3 h-3 animate-spin mr-1" />
                        ) : (
                          <CheckCircle className="w-3 h-3 mr-1" />
                        )}
                        提交判题
                      </Button>
                    )}
                  </div>
                  {judgeResults[i]?.result && (
                    <div
                      className={`text-xs p-2 rounded ${
                        judgeResults[i].result.passed
                          ? 'bg-green-50 text-green-700'
                          : 'bg-red-50 text-red-700'
                      }`}
                    >
                      {judgeResults[i].result.passed ? '✅ 通过' : '❌ 未通过'}：
                      {judgeResults[i].result.reason}
                      {judgeResults[i].result.actual_output && (
                        <div className="mt-1">
                          实际输出：<code>{judgeResults[i].result.actual_output}</code>
                        </div>
                      )}
                    </div>
                  )}
                </CardContent>
              </Card>
            ))}
          </TabsContent>

          <TabsContent value="debate" className="mt-2">
            <Card>
              <CardHeader className="pb-2">
                <CardTitle className="text-sm flex items-center gap-2">
                  {getStatusIcon(resource.debate_report.status)}
                  辩论议会报告 · {resource.debate_report.status}
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-3">
                <div className="flex flex-wrap gap-2">
                  {Object.entries(resource.debate_report.final_votes).map(([agent, verdict]) => (
                    <Badge key={agent} variant="secondary" className={getVerdictColor(verdict)}>
                      {agent}: {verdict}
                    </Badge>
                  ))}
                </div>

                {resource.validation.forbidden_concepts.length > 0 && (
                  <div className="text-xs p-2 rounded bg-red-50 text-red-700">
                    检测到疑似超纲概念：{resource.validation.forbidden_concepts.join('、')}
                  </div>
                )}
                {resource.validation.ast_violations.length > 0 && (
                  <div className="text-xs p-2 rounded bg-red-50 text-red-700">
                    AST 校验问题：{resource.validation.ast_violations.join('、')}
                  </div>
                )}

                <div className="space-y-2">
                  {resource.debate_report.rounds.map((r) => (
                    <div key={r.round} className="rounded-lg border p-3 text-sm">
                      <div className="flex items-center justify-between mb-1">
                        <span className="font-medium">
                          Round {r.round} · {r.agent}
                        </span>
                        <Badge variant="secondary" className={getVerdictColor(r.verdict)}>
                          {r.verdict}
                        </Badge>
                      </div>
                      <p className="text-muted-foreground text-xs">{r.message}</p>
                      {r.suggestion && (
                        <p className="text-xs text-yellow-700 mt-2 bg-yellow-50 p-2 rounded">
                          建议：{r.suggestion}
                        </p>
                      )}
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>
          </TabsContent>
        </Tabs>
      )}

      {!resource && !loading && (
        <p className="text-sm text-muted-foreground">
          输入知识点并点击生成，系统将自动调用多智能体生成个性化学习资源。
        </p>
      )}
    </div>
  )
}
