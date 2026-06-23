import { lazy, Suspense, useEffect, useState } from 'react'
import { BookOpen, Brain, Code2, Loader2, MessageCircle, Network } from 'lucide-react'

import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { ChatPanel } from '@/components/chat/ChatPanel'
import { sessionApi, type SessionResponse } from '@/services/api'

// 按需加载大体积组件，降低首页主 chunk
const KnowledgeGraph = lazy(() => import('@/components/graph/KnowledgeGraph').then((m) => ({ default: m.KnowledgeGraph })))
const PyodideSandbox = lazy(() => import('@/components/code/PyodideSandbox').then((m) => ({ default: m.PyodideSandbox })))
const ResourceViewer = lazy(() => import('@/components/resources/ResourceViewer').then((m) => ({ default: m.ResourceViewer })))

interface SessionStats {
  total_events: number
  chat_count: number
  resource_generated_count: number
  exercise_submitted_count: number
  code_executed_count: number
  exercise_passed_count: number
  exercise_failed_count: number
}

/**
 * 已优化：
 * - [已完成] SSE 流式对话
 * - [已完成] 大体积组件（图谱、沙箱、资源）按路由懒加载
 * TODO:
 * - [待完成] 根据认知风格动态调整布局（场依存/独立 × 视觉/听觉/动觉）
 * - [待完成] 增加学习路径高亮与当前目标提示
 * - [待完成] 接入用户登录与多会话管理
 */

function App() {
  const [session, setSession] = useState<SessionResponse | null>(null)
  const [activeTab, setActiveTab] = useState<'chat' | 'graph' | 'sandbox'>('chat')
  const [stats, setStats] = useState<SessionStats | null>(null)

  const loadStats = async (sessionId: string) => {
    try {
      const res = await sessionApi.getStats(sessionId)
      setStats(res.data)
    } catch {
      setStats(null)
    }
  }

  useEffect(() => {
    // 创建默认会话
    sessionApi.create().then((res) => {
      setSession(res.data)
      loadStats(res.data.session_id)
    })
  }, [])

  useEffect(() => {
    const handler = () => setActiveTab('sandbox')
    window.addEventListener('eduhive:open-sandbox', handler)
    return () => window.removeEventListener('eduhive:open-sandbox', handler)
  }, [])

  useEffect(() => {
    if (!session) return
    const interval = setInterval(() => {
      loadStats(session.session_id)
    }, 5000)
    return () => clearInterval(interval)
  }, [session])

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 to-slate-100 dark:from-slate-950 dark:to-slate-900">
      {/* 顶部导航 */}
      <header className="border-b bg-white/80 backdrop-blur-md dark:bg-slate-950/80 sticky top-0 z-50">
        <div className="container mx-auto px-4 h-16 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-blue-500 to-indigo-600 flex items-center justify-center">
              <Brain className="w-6 h-6 text-white" />
            </div>
            <div>
              <h1 className="text-xl font-bold bg-gradient-to-r from-blue-600 to-indigo-600 bg-clip-text text-transparent">
                智学蜂巢 EduHive
              </h1>
              <p className="text-xs text-muted-foreground">Python 个性化学习系统</p>
            </div>
          </div>

          <div className="flex items-center gap-2">
            <Button
              variant={activeTab === 'chat' ? 'default' : 'ghost'}
              size="sm"
              onClick={() => setActiveTab('chat')}
            >
              <MessageCircle className="w-4 h-4 mr-2" />
              学习对话
            </Button>
            <Button
              variant={activeTab === 'graph' ? 'default' : 'ghost'}
              size="sm"
              onClick={() => setActiveTab('graph')}
            >
              <Network className="w-4 h-4 mr-2" />
              知识图谱
            </Button>
            <Button
              variant={activeTab === 'sandbox' ? 'default' : 'ghost'}
              size="sm"
              onClick={() => setActiveTab('sandbox')}
            >
              <Code2 className="w-4 h-4 mr-2" />
              代码沙箱
            </Button>
          </div>
        </div>
      </header>

      {/* 主体内容 */}
      <main className="container mx-auto px-4 py-6">
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* 左侧：聊天或图谱 */}
          <div className="lg:col-span-2">
            {activeTab === 'chat' && session && (
              <ChatPanel session={session} />
            )}
            <Suspense fallback={<LoadingCard />}>  
              {activeTab === 'graph' && (
                <KnowledgeGraph />
              )}
              {activeTab === 'sandbox' && (
                <PyodideSandbox />
              )}
            </Suspense>
          </div>

          {/* 右侧：画像与资源 */}
          <div className="space-y-6">
            <Card>
              <CardHeader className="pb-3">
                <CardTitle className="text-lg flex items-center gap-2">
                  <Brain className="w-5 h-5 text-blue-500" />
                  学习画像
                </CardTitle>
                <CardDescription>基于对话动态构建</CardDescription>
              </CardHeader>
              <CardContent>
                {session ? (
                  <div className="space-y-3">
                    <ProfileItem label="知识水平" value={`${session.profile.knowledge_level}/5`} />
                    <ProfileItem label="认知风格" value={`${session.profile.cognitive_field === 'dependent' ? '场依存' : '场独立'} · ${session.profile.cognitive_modality === 'visual' ? '视觉' : session.profile.cognitive_modality === 'auditory' ? '听觉' : '动觉'}`} />
                    <ProfileItem label="学习节奏" value={session.profile.learning_pace} />
                    <ProfileItem label="目标导向" value={session.profile.goal_orientation} />
                    <ProfileItem label="已掌握" value={`${session.profile.mastered_concepts.length} 个知识点`} />
                    {stats && (
                      <>
                        <div className="border-t my-2" />
                        <ProfileItem label="对话次数" value={`${stats.chat_count}`} />
                        <ProfileItem label="生成资源" value={`${stats.resource_generated_count}`} />
                        <ProfileItem label="提交练习" value={`${stats.exercise_submitted_count}`} />
                        <ProfileItem label="练习正确率" value={
                          stats.exercise_submitted_count > 0
                            ? `${Math.round((stats.exercise_passed_count / stats.exercise_submitted_count) * 100)}%`
                            : 'N/A'
                        } />
                      </>
                    )}
                  </div>
                ) : (
                  <p className="text-sm text-muted-foreground">正在初始化...</p>
                )}
              </CardContent>
            </Card>

            <Card>
              <CardHeader className="pb-3">
                <CardTitle className="text-lg flex items-center gap-2">
                  <BookOpen className="w-5 h-5 text-green-500" />
                  学习资源
                </CardTitle>
                <CardDescription>多模态个性化生成</CardDescription>
              </CardHeader>
              <CardContent>
                <Suspense fallback={<LoadingSpinner />}>
                  <ResourceViewer sessionId={session?.session_id} />
                </Suspense>
              </CardContent>
            </Card>
          </div>
        </div>
      </main>
    </div>
  )
}

function ProfileItem({ label, value }: { label: string; value: string }) {
  return (
    <div className="flex justify-between items-center text-sm">
      <span className="text-muted-foreground">{label}</span>
      <span className="font-medium">{value}</span>
    </div>
  )
}

function LoadingCard() {
  return (
    <div className="flex h-96 items-center justify-center rounded-xl border bg-white/50 dark:bg-slate-950/50">
      <Loader2 className="h-8 w-8 animate-spin text-blue-500" />
      <span className="ml-2 text-sm text-muted-foreground">正在加载组件...</span>
    </div>
  )
}

function LoadingSpinner() {
  return (
    <div className="flex h-40 items-center justify-center">
      <Loader2 className="h-6 w-6 animate-spin text-blue-500" />
      <span className="ml-2 text-xs text-muted-foreground">正在加载资源...</span>
    </div>
  )
}

export default App
