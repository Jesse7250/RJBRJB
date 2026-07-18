import { memo, useCallback, useEffect, useMemo, useRef, useState, type ComponentType, type FormEvent } from 'react'
import { motion, useMotionValue } from 'framer-motion'
import { Fragment } from 'react'
import {
  BarChart3,
  BookOpen,
  Brain,
  Braces,
  Bot,
  ChevronRight,
  Code2,
  Clock3,
  Download,
  FlaskConical,
  FileUp,
  Hexagon,
  Home,
  Layers3,
  Loader2,
  LockKeyhole,
  Mail,
  MessageSquare,
  Mic,
  Network,
  Play,
  RefreshCw,
  Route,
  Search,
  Send,
  Server,
  ShieldCheck,
  Sparkles,
  Star,
  TerminalSquare,
  Trash2,
  UserRound,
  Volume2,
} from 'lucide-react'

import {
  behaviorApi,
  adminApi,
  authApi,
  codeApi,
  evaluationApi,
  graphApi,
  resourceApi,
  sessionApi,
  teacherApi,
  type AgentResponse,
  type CodeVariable,
  type AdminCourseRecord,
  type CourseMaterial,
  type CourseRecord,
  type GraphData,
  type LearningEvent,
  type LearningPlanResponse,
  type ResourceDetail,
  type ResourceEvolutionResponse,
  type ResourceFeedbackStats,
  type ResourceVersion,
  type SessionResponse,
  type ThinkingStep,
  type UserRole,
} from '@/services/api'
import { SocraticPanel } from '@/components/socratic/SocraticPanel'
import { FloatingAssistant } from '@/components/digital-human/FloatingAssistant'
import { useSparkTTS } from '@/components/digital-human/useSparkTTS'
import { cn } from '@/lib/utils'
import {
  AgentPanel,
  HeatmapPanel,
  HexAvatar,
  LearningMeter,
  Panel,
  PanelHeader,
  ProfilePanel,
  ResourceLibraryPanel,
  StreakCard,
  TopBar,
  WorkspaceDock,
  type ChatMessage,
  type GraphLayoutData,
  type GraphLayoutNode,
  type HealthDetail,
  type HeatmapItem,
  type KnowledgeEdge,
  type MasteryAnalysisResult,
  type NavKey,
  type PathNode,
  type PersonalPathData,
  type PersonalPathNode,
  type SelectedHeatCell,
  type SessionStats,
  type TutorPayload,
} from '@/components/command-center'

const NAV_ITEMS: Array<{ key: NavKey; label: string; icon: ComponentType<{ className?: string }> }> = [
  { key: 'profile', label: '学习画像', icon: UserRound },
  { key: 'graph', label: '知识图谱', icon: Hexagon },
  { key: 'resources', label: '学习资源', icon: BookOpen },
  { key: 'chat', label: '学习对话', icon: MessageSquare },
  { key: 'code', label: '代码沙箱', icon: Code2 },
  { key: 'progress', label: '掌握进度', icon: BarChart3 },
]

type CourseCard = {
  id: string
  backendCourseId?: string
  workspace?: 'python' | 'materials' | 'empty'
  title: string
  category: string
  level: string
  teacher: string
  duration: string
  status: 'ready' | 'empty'
  accent: 'teal' | 'orange' | 'blue' | 'green'
  summary: string
  tags: string[]
}

function toPublishedCourseCard(course: CourseRecord): CourseCard {
  return {
    id: `course-${course.course_id}`,
    backendCourseId: course.course_id,
    workspace: 'materials',
    title: course.title,
    category: course.category,
    level: '教师发布',
    teacher: course.teacher_username || '教师',
    duration: '可查看资料',
    status: 'ready',
    accent: 'teal',
    summary: course.summary || '教师上传的课程资料与说明。',
    tags: ['教师发布', '资料可见'],
  }
}

function formatFileSize(bytes: number) {
  if (!bytes) return '0 KB'
  if (bytes < 1024 * 1024) return `${Math.max(1, Math.round(bytes / 1024))} KB`
  return `${(bytes / 1024 / 1024).toFixed(1)} MB`
}

function getCourseStatusLabel(status: string) {
  switch (status) {
    case 'published':
      return '已发布'
    case 'pending_review':
      return '待审核'
    case 'archived':
      return '已归档'
    default:
      return '草稿'
  }
}

type ResourcePanelCacheEntry = {
  resource: ResourceDetail | null
  status: string
  thinkingSteps: ThinkingStep[]
  versions: ResourceVersion[]
  evolution: ResourceEvolutionResponse | null
  feedbackStats: ResourceFeedbackStats | null
  cachedAt: number
}

const COURSE_CATALOG: CourseCard[] = [
  {
    id: 'python',
    workspace: 'python',
    title: 'Python 程序设计基础',
    category: '程序设计',
    level: '入门到进阶',
    teacher: '智学蜂巢教研组',
    duration: '6 个模块',
    status: 'ready',
    accent: 'teal',
    summary: '从基础语法、控制流到文件操作，配合练习、代码运行和个性化辅导完成入门训练。',
    tags: ['知识图谱', '代码练习', 'AI 辅导'],
  },
  {
    id: 'data-structure',
    workspace: 'empty',
    title: '数据结构可视化训练营',
    category: '计算机基础',
    level: '进阶',
    teacher: '算法教研组',
    duration: '8 个模块',
    status: 'empty',
    accent: 'blue',
    summary: '用动画和案例理解数组、链表、栈、队列、树与图。',
    tags: ['动画演示', '算法思维', '待开放'],
  },
  {
    id: 'ai-literacy',
    workspace: 'empty',
    title: '人工智能通识与提示词实践',
    category: 'AI 通识',
    level: '零基础',
    teacher: 'AI 创新中心',
    duration: '5 个模块',
    status: 'empty',
    accent: 'orange',
    summary: '从大模型能力边界、提示词方法到学习场景应用，建立 AI 使用素养。',
    tags: ['大模型', '提示词', '待开放'],
  },
  {
    id: 'english-speaking',
    workspace: 'empty',
    title: '英语口语情景对话',
    category: '语言学习',
    level: '日常交流',
    teacher: '语言训练实验室',
    duration: '12 个场景',
    status: 'empty',
    accent: 'green',
    summary: '围绕校园、面试、旅行和学术交流构建口语训练闭环。',
    tags: ['情景对话', '听说训练', '待开放'],
  },
  {
    id: 'math-modeling',
    workspace: 'empty',
    title: '数学建模方法入门',
    category: '数理基础',
    level: '竞赛预备',
    teacher: '建模工作坊',
    duration: '7 个专题',
    status: 'empty',
    accent: 'teal',
    summary: '覆盖模型假设、数据处理、优化求解和论文表达。',
    tags: ['建模', '数据分析', '待开放'],
  },
  {
    id: 'web-design',
    workspace: 'empty',
    title: '前端交互设计基础',
    category: '软件工程',
    level: '实践课',
    teacher: '交互设计教研组',
    duration: '9 个项目',
    status: 'empty',
    accent: 'blue',
    summary: '从布局、组件状态到可用性设计，完成一个真实 Web 应用。',
    tags: ['React', '交互设计', '待开放'],
  },
]

const FALLBACK_TARGET_CONCEPT = '变量与赋值'

function getInitialTargetConcept() {
  if (typeof window === 'undefined') return FALLBACK_TARGET_CONCEPT
  // hash 路由下参数位于 # 之后，需从 hash 中解析
  const hashQuery = window.location.hash.includes('?')
    ? window.location.hash.split('?')[1]
    : ''
  const params = new URLSearchParams(window.location.search || hashQuery)
  return (
    params.get('target_concept') ||
    params.get('target') ||
    window.localStorage.getItem('eduhive.target_concept') ||
    FALLBACK_TARGET_CONCEPT
  ).trim()
}

const SAMPLE_CODE = `# 读取文件示例
file_path = 'sample.txt'
with open(file_path, 'r', encoding='utf-8') as f:
    content = f.read()
    print('文件内容:')
    print(content)

# 按行读取
with open(file_path, 'r', encoding='utf-8') as f:
    lines = f.readlines()
    print('\\n按行读取:')
    for i, line in enumerate(lines, 1):
        print(f'{i}: {line.strip()}')`

const SAMPLE_OUTPUT = `文件内容:
Hello, EduHive!
今天学习 Python 文件操作。
继续加油!

按行读取:
1: Hello, EduHive!
2: 今天学习 Python 文件操作。
3: 继续加油!`

const SAMPLE_VARIABLES: CodeVariable[] = [
  { name: 'file_path', type: 'str', value: "'sample.txt'", size: 10 },
  { name: 'content', type: 'str', value: "'Hello, EduHive!\\n今天学习 Python 文件操作。\\n继续加油!'", size: 39 },
  { name: 'lines', type: 'list', value: "['Hello, EduHive!\\n', '今天学习 Python 文件操作。\\n', '继续加油!']", size: 3 },
  { name: 'i', type: 'int', value: '3' },
  { name: 'line', type: 'str', value: "'继续加油!'", size: 5 },
]

function iconForConcept(name: string, module?: string): ComponentType<{ className?: string }> {
  const text = `${name}${module ?? ''}`
  if (/文件|IO|输入|输出/.test(text)) return TerminalSquare
  if (/函数|方法/.test(text)) return Network
  if (/循环|迭代/.test(text)) return RefreshCw
  if (/条件|判断|分支/.test(text)) return Route
  if (/异常|错误/.test(text)) return ShieldCheck
  if (/模块|包|库/.test(text)) return Server
  if (/列表|字典|数据|变量|类型/.test(text)) return Layers3
  if (/代码|语法|基础/.test(text)) return BookOpen
  return FlaskConical
}

function buildPathNodes(graph: GraphData | null, heatmap: HeatmapItem[]): PathNode[] {
  const mastery = new Map(heatmap.map((item) => [item.concept, Math.round(item.mastery_probability * 100)]))
  const fallbackNodes = [
    { id: 'Python 基础语法', name: 'Python 基础语法', module: '基础', difficulty: 1 },
    { id: '数据类型与变量', name: '数据类型与变量', module: '基础', difficulty: 1 },
    { id: '输入与输出', name: '输入与输出', module: '基础', difficulty: 2 },
    { id: '变量基础', name: '变量基础', module: '基础', difficulty: 2 },
    { id: '条件判断', name: '条件判断', module: '控制流', difficulty: 3 },
    { id: '循环结构', name: '循环结构', module: '控制流', difficulty: 3 },
    { id: '函数封装', name: '函数封装', module: '函数', difficulty: 4 },
    { id: '文件读写', name: '文件读写', module: '文件', difficulty: 4 },
    { id: '异常处理', name: '异常处理', module: '工程化', difficulty: 5 },
    { id: '模块与包', name: '模块与包', module: '工程化', difficulty: 5 },
    { id: '列表与字典', name: '列表与字典', module: '数据结构', difficulty: 3 },
  ]
  const fallbackEdges: KnowledgeEdge[] = [
    { source: 'Python 基础语法', target: '变量基础', strength: 0.8 },
    { source: '数据类型与变量', target: '变量基础', strength: 0.8 },
    { source: '输入与输出', target: '文件读写', strength: 0.8 },
    { source: '变量基础', target: '条件判断', strength: 0.8 },
    { source: '条件判断', target: '循环结构', strength: 0.8 },
    { source: '循环结构', target: '函数封装', strength: 0.8 },
    { source: '函数封装', target: '文件读写', strength: 0.8 },
    { source: '异常处理', target: '文件读写', strength: 0.8 },
    { source: '模块与包', target: '文件读写', strength: 0.8 },
  ]

  const sourceNodes = graph?.nodes.length ? graph.nodes : fallbackNodes
  const sourceEdges = graph?.edges.length ? graph.edges : fallbackEdges
  const names = sourceNodes.map((node) => node.name)
  const nameSet = new Set(names)
  const indegree = new Map(names.map((name) => [name, 0]))
  const outgoing = new Map<string, string[]>()

  sourceEdges.forEach((edge) => {
    if (!nameSet.has(edge.source) || !nameSet.has(edge.target)) return
    outgoing.set(edge.source, [...(outgoing.get(edge.source) ?? []), edge.target])
    indegree.set(edge.target, (indegree.get(edge.target) ?? 0) + 1)
  })

  const levels = new Map<string, number>()
  const queue = names.filter((name) => (indegree.get(name) ?? 0) === 0)
  queue.forEach((name) => levels.set(name, 0))

  for (let index = 0; index < queue.length; index += 1) {
    const current = queue[index]
    const currentLevel = levels.get(current) ?? 0
    for (const next of outgoing.get(current) ?? []) {
      levels.set(next, Math.max(levels.get(next) ?? 0, currentLevel + 1))
      indegree.set(next, (indegree.get(next) ?? 1) - 1)
      if ((indegree.get(next) ?? 0) === 0) queue.push(next)
    }
  }

  sourceNodes.forEach((node, index) => {
    if (!levels.has(node.name)) {
      levels.set(node.name, Math.max(0, (node.difficulty ?? 3) - 1) + (index % 2))
    }
  })

  const grouped = new Map<number, typeof sourceNodes>()
  sourceNodes.forEach((node) => {
    const level = levels.get(node.name) ?? 0
    grouped.set(level, [...(grouped.get(level) ?? []), node])
  })
  const sortedLevels = [...grouped.keys()].sort((a, b) => a - b)
  const levelIndex = new Map(sortedLevels.map((level, index) => [level, index]))
  const levelStartColumn = new Map<number, number>()
  let totalColumns = 0
  sortedLevels.forEach((level) => {
    const columnCount = Math.max(1, Math.ceil((grouped.get(level)?.length ?? 1) / 3))
    levelStartColumn.set(level, totalColumns)
    totalColumns += columnCount + 1
  })
  const maxColumn = Math.max(1, totalColumns - 1)

  return sourceNodes.map((node) => {
    const rawLevel = levels.get(node.name) ?? 0
    const level = levelIndex.get(rawLevel) ?? 0
    const siblings = [...(grouped.get(rawLevel) ?? [node])].sort((a, b) => {
      const moduleCompare = (a.module ?? '').localeCompare(b.module ?? '')
      return moduleCompare || a.name.localeCompare(b.name)
    })
    const siblingIndex = siblings.findIndex((item) => item.name === node.name)
    const localColumn = Math.floor(Math.max(0, siblingIndex) / 3)
    const rowInColumn = Math.max(0, siblingIndex) % 3
    const rowsInColumn = Math.min(3, siblings.length - localColumn * 3)
    const rowSlots = rowsInColumn === 1 ? [50] : rowsInColumn === 2 ? [28, 72] : [16, 50, 84]
    const y = Math.min(90, Math.max(10, rowSlots[rowInColumn] + (level % 2 === 0 ? -2 : 2)))
    const column = (levelStartColumn.get(rawLevel) ?? level) + localColumn
    const x = 4 + column * (92 / maxColumn)
    const value = mastery.get(node.name) ?? Math.max(30, 94 - (node.difficulty ?? 3) * 8)
    return {
      id: node.id || node.name,
      title: node.name,
      module: node.module,
      difficulty: node.difficulty,
      mastery: value,
      x,
      y,
      state: value >= 80 ? 'mastered' : value >= 58 ? 'learning' : 'waiting',
      icon: iconForConcept(node.name, node.module),
    }
  })
}

function normalizePathState(node: PersonalPathNode | undefined, mastery: number): PathNode['state'] {
  if (node?.is_current || node?.state === 'current') return 'current'
  if (node?.is_mastered || node?.state === 'mastered' || mastery >= 80) return 'mastered'
  if (node?.state === 'waiting') return 'waiting'
  return mastery >= 58 ? 'learning' : 'waiting'
}

function buildBackendPathNodes(layout: GraphLayoutData | null, personalPath: PersonalPathData | null, heatmap: HeatmapItem[]): PathNode[] {
  if (!layout?.nodes?.length) return []
  const visualGraph: GraphData = {
    nodes: layout.nodes.map((node) => ({
      id: node.id,
      name: node.name,
      module: node.module,
      difficulty: node.difficulty,
    })),
    edges: layout.edges,
  }
  const visualNodes = buildPathNodes(visualGraph, heatmap)
  const visualByName = new Map(visualNodes.map((node) => [node.title, node]))
  const masteryFromHeatmap = new Map(heatmap.map((item) => [item.concept, Math.round(item.mastery_probability * 100)]))
  const pathByName = new Map<string, PersonalPathNode>()
  for (const node of personalPath?.path_nodes ?? []) {
    pathByName.set(node.name || node.id, node)
  }

  return layout.nodes.map((node: GraphLayoutNode) => {
    const visualNode = visualByName.get(node.name)
    const pathNode = pathByName.get(node.name) || pathByName.get(node.id)
    const mastery = pathNode?.mastery_probability !== undefined
      ? Math.round(pathNode.mastery_probability * 100)
      : masteryFromHeatmap.get(node.name) ?? Math.max(30, 94 - (node.difficulty ?? 3) * 8)
    return {
      id: node.id || node.name,
      title: node.name,
      module: node.module,
      difficulty: node.difficulty,
      mastery,
      x: visualNode?.x ?? 50,
      y: visualNode?.y ?? 50,
      state: normalizePathState(pathNode, mastery),
      icon: iconForConcept(node.name, node.module),
    }
  })
}

function edgePath(source: PathNode, target: PathNode) {
  const midX = (source.x + target.x) / 2
  const lift = source.y > target.y ? -8 : 8
  return `M${source.x} ${source.y} C${midX} ${source.y + lift}, ${midX} ${target.y - lift}, ${target.x} ${target.y}`
}

function buildPathEdgeKey(source: string, target: string) {
  return `${source}->${target}`
}

function inferCodeVariables(code: string, output: string): CodeVariable[] {
  const variables = new Map<string, CodeVariable>()
  const setVariable = (name: string, type: string, value: string, size?: number | null) => {
    if (!/^[A-Za-z_]\w*$/.test(name)) return
    variables.set(name, { name, type, value, size })
  }
  const inferType = (value: string) => {
    if (/^(['"]).*\1$/.test(value)) return 'str'
    if (/^-?\d+$/.test(value)) return 'int'
    if (/^-?\d+\.\d+$/.test(value)) return 'float'
    if (/^(True|False)$/.test(value)) return 'bool'
    if(/^\[.*\]$/.test(value)) return 'list'
    if (/^\{.*\}$/.test(value)) return 'dict'
    if (/^\(.*\)$/.test(value)) return 'tuple'
    return 'expr'
  }

  code.split('\n').forEach((rawLine) => {
    const line = rawLine.trim()
    if (!line || line.startsWith('#')) return
    const match = line.match(/^([A-Za-z_]\w*)\s*=\s*(.+)$/)
    if (!match) return
    const value = match[2].replace(/\s+#.*$/, '').trim()
    if (!value || value.includes('==')) return
    setVariable(match[1], inferType(value), value)
  })

  const contentMatch = output.match(/文件内容:\s*\n([\s\S]*?)(?:\n\s*按行读取:|$)/)
  if (contentMatch?.[1]) {
    const content = contentMatch[1].trimEnd()
    const lines = content.split(/\r?\n/)
    setVariable('content', 'str', JSON.stringify(content), content.length)
    setVariable('lines', 'list', JSON.stringify(lines), lines.length)
  }

  const numberedLines = [...output.matchAll(/^\s*(\d+):\s*(.+)$/gm)]
  if (numberedLines.length) {
    const last = numberedLines[numberedLines.length - 1]
    setVariable('i', 'int', last[1])
    setVariable('line', 'str', JSON.stringify(last[2]), last[2].length)
  }

  return [...variables.values()]
}

function normalizeCodeVariables(input: unknown): CodeVariable[] {
  if (!input) return []
  const source = Array.isArray(input)
    ? input
    : typeof input === 'object'
      ? Object.entries(input as Record<string, unknown>).map(([name, value]) => {
          if (value && typeof value === 'object' && ('name' in value || 'value' in value || 'type' in value)) {
            return { name, ...(value as Record<string, unknown>) }
          }
          return { name, value, type: typeof value }
        })
      : []
  const normalized: CodeVariable[] = []
  source.forEach((item) => {
    if (!item || typeof item !== 'object') return
    const raw = item as Record<string, unknown>
    const name = String(raw.name ?? raw.variable ?? raw.key ?? '').trim()
    if (!name) return
    const rawValue = raw.value ?? raw.preview ?? raw.repr ?? ''
    const sizeValue = raw.size ?? raw.length
    normalized.push({
      name,
      type: String(raw.type ?? raw.kind ?? typeof rawValue),
      value: typeof rawValue === 'string' ? rawValue : JSON.stringify(rawValue),
      size: typeof sizeValue === 'number' ? sizeValue : null,
    })
  })
  return normalized
}

function extractCodeVariables(payload: unknown): CodeVariable[] {
  if (!payload || typeof payload !== 'object') return []
  const data = payload as Record<string, unknown>
  const candidates = [
    data.variables,
    data.locals,
    data.variable_snapshot,
    data.variable_snapshots,
    data.result && typeof data.result === 'object' ? (data.result as Record<string, unknown>).variables : undefined,
    data.data && typeof data.data === 'object' ? (data.data as Record<string, unknown>).variables : undefined,
  ]
  for (const candidate of candidates) {
    const normalized = normalizeCodeVariables(candidate)
    if (normalized.length) return normalized
  }
  return []
}

function createChatMessage(role: ChatMessage['role'], content: string, agentName?: string, isStreaming = false): ChatMessage {
  return {
    id: `${role}-${Date.now()}-${Math.random().toString(36).slice(2)}`,
    role,
    content,
    agentName,
    isStreaming,
    timestamp: new Date().toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit' }),
  }
}

function tryParseJsonString(value: unknown): unknown {
  if (typeof value !== 'string') return value
  try {
    return JSON.parse(value)
  } catch {
    return value
  }
}

function findTextField(value: unknown, depth = 0): string {
  if (depth > 4 || value == null) return ''
  const parsed = typeof value === 'string' ? tryParseJsonString(value) : value
  if (typeof parsed === 'string') return parsed.trim()
  if (Array.isArray(parsed)) {
    for (const item of parsed) {
      const text = findTextField(item, depth + 1)
      if (text) return text
    }
    return ''
  }
  if (typeof parsed !== 'object') return ''
  const record = parsed as Record<string, unknown>
  for (const key of ['message', 'response_message', 'question', 'answer', 'text', 'reply', 'content']) {
    const candidate = record[key]
    if (typeof candidate === 'string' && candidate.trim()) return candidate.trim()
  }
  for (const key of ['payload', 'data', 'result', 'socratic', 'response']) {
    const text = findTextField(record[key], depth + 1)
    if (text) return text
  }
  return ''
}

function extractAgentText(response?: AgentResponse | null, preferredModality?: 'text' | 'visual' | 'auditory' | 'kinesthetic') {
  const rawContent = response?.content
  if (!rawContent) return ''
  const content = typeof rawContent === 'string' ? tryParseJsonString(rawContent) : rawContent
  if (typeof content === 'string') return content
  const directText = findTextField(content)
  if (directText) {
    const profile = content.profile || response?.profile_update
    if (!profile) return String(directText)
    const mastered = Array.isArray(profile.mastered_concepts) && profile.mastered_concepts.length
      ? `已掌握：${profile.mastered_concepts.join('、')}`
      : ''
    const modalityValue = preferredModality || profile.cognitive_modality
    const modalityLabel: Record<string, string> = { text: '文字型', visual: '视觉型', auditory: '听觉型', kinesthetic: '动觉型' }
    const modality = modalityLabel[modalityValue] || ''
    const profileLine = [
      modality && `认知风格：${modality}`,
      profile.learning_pace && `节奏：${profile.learning_pace}`,
      mastered,
    ].filter(Boolean).join('；')
    return profileLine ? `${directText}\n\n画像更新：${profileLine}` : String(directText)
  }
  if (content.profile) return '学习画像已更新，我会根据你的知识水平和认知风格调整后续讲解。'
  return '后端已返回结构化结果，当前没有可直接展示的自然语言回复。'
}

function asObject(value: unknown): Record<string, any> | null {
  return value && typeof value === 'object' ? value as Record<string, any> : null
}

function optionalText(value: unknown) {
  return typeof value === 'string' && value.trim() ? value.trim() : undefined
}

function extractTutorPayload(response?: AgentResponse | null): TutorPayload | undefined {
  const rawContent = response?.content
  const parsed = typeof rawContent === 'string' ? tryParseJsonString(rawContent) : rawContent
  const baseContent = asObject(parsed)
  const content = asObject(baseContent?.socratic) || asObject(baseContent?.payload) || asObject(baseContent?.data) || baseContent
  if (!content) return undefined

  const looksLikeTutor =
    response?.response_type === 'tutor' ||
    response?.agent_name === 'Socrates' ||
    Boolean(content.question || content.hint || content.can_provide_answer || content.canProvideAnswer || content.stage)
  if (!looksLikeTutor) return undefined

  const question = optionalText(content.question) || optionalText(content.message) || optionalText(content.response_message)
  if (!question) return undefined

  return {
    question,
    hint: optionalText(content.hint),
    answer: optionalText(content.answer),
    canProvideAnswer: Boolean(content.can_provide_answer || content.canProvideAnswer),
    stage: optionalText(content.stage) || response?.response_type,
  }
}

function shouldUseSocraticFallback(userMessage: string) {
  const text = userMessage.trim()
  if (!text) return false
  return /(？|\?|什么|不会|不懂|不理解|为什么|怎么|如何|哪里错|报错|错误|问题|帮我|提示|引导|解释|区别|用法|语法|运行失败|看不懂|练习题|做错|答错|没掌握|没理解|变量|循环|函数|条件|列表|字典|文件读写|代码)/i.test(text)
}

function looksLikeProfileUpdateResponse(response?: AgentResponse | null) {
  const profile = response?.content?.profile || response?.profile_update
  return Boolean(profile || response?.agent_name === 'Profiler' || response?.response_type === 'profile_update' || response?.response_type === 'profiler')
}

function createSocraticFallbackPayload(text: string, concept: string, userMessage: string): TutorPayload | undefined {
  const cleanText = text.trim()
  if (!cleanText || !shouldUseSocraticFallback(userMessage)) return undefined
  const looksLikeInstructionEcho = /请继续用苏格拉底式|不要直接给答案|继续.*引导/.test(cleanText)
  const question = looksLikeInstructionEcho
    ? `换个角度看「${concept}」：你现在最不确定的是概念含义、代码写法，还是运行结果？`
    : cleanText
  return {
    question,
    hint: `先围绕「${concept}」说出你的判断依据，再继续下一步引导。`,
    canProvideAnswer: false,
    stage: 'guided',
  }
}

function extractProfileFromResponse(response?: AgentResponse | null) {
  const profile = response?.content?.profile || response?.profile_update
  return profile && typeof profile === 'object' ? profile as Partial<SessionResponse['profile']> : null
}

function App() {
  const [courseMode, setCourseMode] = useState<'portal' | 'python' | 'empty' | 'teacher' | 'admin'>(() => {
    if (typeof window === 'undefined') return 'portal'
    if (window.location.hash.startsWith('#/teacher')) return 'teacher'
    if (window.location.hash.startsWith('#/admin')) return 'admin'
    if (window.location.hash.startsWith('#/course/python')) return 'python'
    if (window.location.hash.startsWith('#/course/')) return 'empty'
    return 'portal'
  })
  const [selectedCourseId, setSelectedCourseId] = useState(() => {
    if (typeof window === 'undefined') return 'python'
    const match = window.location.hash.match(/^#\/course\/([^/]+)/)
    return match?.[1] || 'python'
  })
  const [activeNav, setActiveNav] = useState<NavKey>('graph')
  const [session, setSession] = useState<SessionResponse | null>(null)
  const [stats, setStats] = useState<SessionStats | null>(null)
  const [agentTraces, setAgentTraces] = useState<any[]>([])
  const [graph, setGraph] = useState<GraphData | null>(null)
  const [graphLayout, setGraphLayout] = useState<GraphLayoutData | null>(null)
  const [personalPath, setPersonalPath] = useState<PersonalPathData | null>(null)
  const [heatmap, setHeatmap] = useState<HeatmapItem[]>([])
  const [health, setHealth] = useState<HealthDetail | null>(null)
  const [targetConcept, setTargetConcept] = useState(getInitialTargetConcept)
  const [selectedConcept, setSelectedConcept] = useState(targetConcept)
  const [selectedNodeId, setSelectedNodeId] = useState(targetConcept)
  const [resourceConcept, setResourceConcept] = useState(targetConcept)
  const [plannedPath, setPlannedPath] = useState<string[]>(['变量基础', '条件判断', '循环结构', '函数封装', targetConcept])
  const [showGraphDetail, setShowGraphDetail] = useState(true)
  const [graphFocusNonce, setGraphFocusNonce] = useState(0)
  const [selectedHeatCell, setSelectedHeatCell] = useState<SelectedHeatCell | null>(null)
  const [bktDetail, setBktDetail] = useState<any | null>(null)
  const [bktLoading, setBktLoading] = useState(false)
  const [masteryAnalyzing, setMasteryAnalyzing] = useState(false)
  const [masteryAnalysis, setMasteryAnalysis] = useState<MasteryAnalysisResult | null>(null)
  const [workspaceNote, setWorkspaceNote] = useState('点击知识节点、Agent 或工具按钮开始联动。')
  const [thinkingSteps, setThinkingSteps] = useState<ThinkingStep[]>([])
  const [versions, setVersions] = useState<ResourceVersion[]>([])
  const [learningPlan, setLearningPlan] = useState<LearningPlanResponse | null>(null)
  const [learningEvents, setLearningEvents] = useState<LearningEvent[]>([])
  const [resourceEvolution, setResourceEvolution] = useState<ResourceEvolutionResponse | null>(null)
  const [feedbackStats, setFeedbackStats] = useState<ResourceFeedbackStats | null>(null)
  const [resourcePackage, setResourcePackage] = useState<ResourceDetail | null>(null)
  const [resourcePanelLoading, setResourcePanelLoading] = useState(false)
  const [conceptDetail, setConceptDetail] = useState<any | null>(null)
  const [styleMode, setStyleMode] = useState<'text' | 'visual' | 'auditory' | 'kinesthetic'>('text')
  const styleModeRef = useRef<'text' | 'visual' | 'auditory' | 'kinesthetic'>('text')
  const [chatInput, setChatInput] = useState(() => `我想学习 ${targetConcept}`)
  const [chatMessages, setChatMessages] = useState<ChatMessage[]>([
    createChatMessage('assistant', `你已经掌握了前置知识，接下来我们学习「${targetConcept}」。你可以直接提问，我会结合学习画像、知识图谱和练习记录进行辅导。`, 'Socrates'),
  ])
  const [chatLoading, setChatLoading] = useState(false)
  const [code, setCode] = useState(SAMPLE_CODE)
  const [codeOutput, setCodeOutput] = useState(SAMPLE_OUTPUT)
  const [codeVariables, setCodeVariables] = useState<CodeVariable[]>(SAMPLE_VARIABLES)
  const [codeLoading, setCodeLoading] = useState(false)
  const [resourceStatus, setResourceStatus] = useState('资源生成接口待命')
  const [resourceLoading, setResourceLoading] = useState(false)
  const [publishedCourseCards, setPublishedCourseCards] = useState<CourseCard[]>([])
  const resourcePanelCacheRef = useRef<Map<string, ResourcePanelCacheEntry>>(new Map())
  const resourcePanelPendingRef = useRef<Map<string, Promise<ResourcePanelCacheEntry>>>(new Map())
  const [authUser, setAuthUser] = useState(() => {
    if (typeof window === 'undefined') return ''
    return window.localStorage.getItem('eduhive.username') ?? ''
  })
  const [authRole, setAuthRole] = useState<UserRole>(() => {
    if (typeof window === 'undefined') return 'student'
    return (window.localStorage.getItem('eduhive.role') as UserRole) || 'student'
  })
  const [loginRole, setLoginRole] = useState<UserRole>('student')

  useEffect(() => {
    styleModeRef.current = styleMode
  }, [styleMode])

  const mergeSessionProfile = (profilePatch: Partial<SessionResponse['profile']>) => {
    setSession((current) => current ? {
      ...current,
      profile: {
        ...current.profile,
        ...profilePatch,
        cognitive_modality: styleModeRef.current,
      },
    } : current)
  }

  const applyResourceCache = useCallback((concept: string, entry: ResourcePanelCacheEntry, note = 'cache') => {
    setResourceConcept(concept)
    setResourcePackage(entry.resource)
    setThinkingSteps(entry.thinkingSteps)
    setVersions(entry.versions)
    setResourceEvolution(entry.evolution)
    setFeedbackStats(entry.feedbackStats)
    setResourceStatus(entry.status)
    setWorkspaceNote(
      entry.resource
        ? `已从本地缓存载入「${concept}」资源包`
        : `「${concept}」暂无已生成资源，请先生成。`,
    )
    if (session && note !== 'silent') {
      behaviorApi.log(session.session_id, 'resource_cache_hit', concept, { surface: note }).catch(() => undefined)
    }
  }, [session])
  const [loginUsername, setLoginUsername] = useState(() => {
    if (typeof window === 'undefined') return ''
    return window.localStorage.getItem('eduhive.username') ?? ''
  })
  const [loginPassword, setLoginPassword] = useState('')
  const [loginMode, setLoginMode] = useState<'login' | 'register'>('login')
  const [authLoading, setAuthLoading] = useState(false)
  const [loginStatus, setLoginStatus] = useState(() => {
    if (typeof window === 'undefined') return '请登录账号。'
    const savedUser = window.localStorage.getItem('eduhive.username')
    return savedUser ? `已登录：${savedUser}` : '请登录账号。'
  })

  useEffect(() => {
    let cancelled = false
    teacherApi.getPublishedCourses()
      .then((res) => {
        if (!cancelled) {
          setPublishedCourseCards(res.data.courses.map(toPublishedCourseCard))
        }
      })
      .catch(() => {
        if (!cancelled) setPublishedCourseCards([])
      })
    return () => {
      cancelled = true
    }
  }, [])

  useEffect(() => {
    const syncRoute = () => {
      const hash = window.location.hash || '#/portal'
      if (hash.startsWith('#/teacher')) {
        setCourseMode('teacher')
        return
      }
      if (hash.startsWith('#/admin')) {
        setCourseMode('admin')
        return
      }
      if (hash === '#/portal' || hash === '#/' || hash === '') {
        setCourseMode('portal')
        return
      }

      const courseMatch = hash.match(/^#\/course\/([^/]+)(?:\/([^?]+))?/)
      if (courseMatch) {
        const courseId = courseMatch[1]
        const navKey = courseMatch[2] as NavKey | undefined
        setSelectedCourseId(courseId)
        setCourseMode(courseId === 'python' ? 'python' : 'empty')
        if (navKey && NAV_ITEMS.some((item) => item.key === navKey)) setActiveNav(navKey)
        return
      }

      const key = hash.replace('#/', '') as NavKey
      if (NAV_ITEMS.some((item) => item.key === key)) {
        setCourseMode('python')
        setSelectedCourseId('python')
        setActiveNav(key)
      }
    }
    syncRoute()
    window.addEventListener('hashchange', syncRoute)
    return () => window.removeEventListener('hashchange', syncRoute)
  }, [])

  const navigateTo = useCallback((nav: NavKey, note?: string) => {
    const wasGraph = activeNav === 'graph'
    setCourseMode('python')
    setSelectedCourseId('python')
    setActiveNav(nav)
    if (nav === 'graph') {
      setShowGraphDetail(true)
      if (!wasGraph) setGraphFocusNonce((value) => value + 1)
    }
    if (window.location.hash !== `#/course/python/${nav}`) {
      window.location.hash = `/course/python/${nav}`
    }
    setWorkspaceNote(note ?? `已切换到「${NAV_ITEMS.find((item) => item.key === nav)?.label ?? '工作台'}」。`)
  }, [activeNav])

  const openPortal = () => {
    setCourseMode('portal')
    window.location.hash = '/portal'
  }

  const openCourse = (course: CourseCard) => {
    setSelectedCourseId(course.id)
    if (course.workspace === 'python' || course.id === 'python') {
      setCourseMode('python')
      setActiveNav('graph')
      setShowGraphDetail(true)
      setGraphFocusNonce((value) => value + 1)
      window.location.hash = '/course/python/graph'
      setWorkspaceNote('已进入 Python 课程，建议先查看知识图谱并规划学习路径。')
      return
    }

    setCourseMode('empty')
    window.location.hash = `/course/${course.id}`
  }

  const submitPortalAuth = async (continueCourse?: CourseCard) => {
    if (authUser) {
      setLoginStatus(`已登录：${authUser}`)
      if (continueCourse) openCourse(continueCourse)
      return
    }

    const username = loginUsername.trim()
    if (!username || !loginPassword.trim()) {
      setLoginStatus('请输入账号和密码。')
      return
    }

    setAuthLoading(true)
    setLoginStatus(loginMode === 'register' ? '正在注册账号...' : '正在登录...')
    try {
      const response = loginMode === 'register'
        ? await authApi.register(username, loginPassword, loginRole)
        : await authApi.login(username, loginPassword)
      const { access_token, username: returnedUsername, role } = response.data
      if (loginMode === 'login' && role !== loginRole) {
        throw new Error(`账号角色与当前入口不匹配，请切换到${role === 'student' ? '学生' : role === 'teacher' ? '教师' : '管理员'}入口登录。`)
      }
      window.localStorage.setItem('eduhive.auth_token', access_token)
      window.localStorage.setItem('eduhive.username', returnedUsername || username)
      window.localStorage.setItem('eduhive.role', role || 'student')
      setAuthUser(returnedUsername || username)
      setAuthRole(role || 'student')
      setLoginUsername(returnedUsername || username)
      setLoginPassword('')
      setLoginStatus(loginMode === 'register' ? '注册成功，已自动登录。' : '登录成功。')
      if (role === 'teacher') {
        setCourseMode('teacher')
        window.location.hash = '/teacher'
      } else if (role === 'admin') {
        setCourseMode('admin')
        window.location.hash = '/admin'
      } else if (continueCourse) {
        openCourse(continueCourse)
      }
    } catch (error: any) {
      const detail = error?.response?.data?.detail
      setLoginStatus(typeof detail === 'string' ? detail : error?.message || '登录暂时失败，请检查账号密码后重试。')
    } finally {
      setAuthLoading(false)
    }
  }

  const logoutPortal = async () => {
    setAuthLoading(true)
    try {
      if (window.localStorage.getItem('eduhive.auth_token')) await authApi.logout()
    } catch {
      // 本地退出优先，后端 token 黑名单失败时不阻断用户操作。
    } finally {
      window.localStorage.removeItem('eduhive.auth_token')
      window.localStorage.removeItem('eduhive.username')
      window.localStorage.removeItem('eduhive.role')
      setAuthUser('')
      setAuthRole('student')
      setLoginPassword('')
      setLoginStatus('已退出登录。')
      setCourseMode('portal')
      window.location.hash = '/portal'
      setAuthLoading(false)
    }
  }

  useEffect(() => {
    if (activeNav !== 'code' || codeVariables.length) return
    const inferred = inferCodeVariables(code, codeOutput)
    if (inferred.length) setCodeVariables(inferred)
  }, [activeNav, code, codeOutput, codeVariables.length])

  useEffect(() => {
    let cancelled = false

    async function bootstrap() {
      try {
        const [sessionRes, graphRes, layoutRes, healthRes] = await Promise.all([
          sessionApi.create(targetConcept),
          graphApi.getGraph(),
          graphApi.getLayout().catch(() => null),
          fetch('/health/detail').then((res) => res.json()).catch(() => null),
        ])

        if (cancelled) return
        const nextTarget = sessionRes.data.target_concept || targetConcept
        const validTargets = new Set(graphRes.data.nodes.map((n) => n.name))
        const targetNode = graphRes.data.nodes.find((n) => n.name === nextTarget)
        const isBeginnerTarget = targetNode && ((targetNode.module && targetNode.module.includes('基础')) || targetNode.difficulty <= 2)
        const fallbackTarget = (() => {
          const basics = graphRes.data.nodes.filter((n) => (n.module && n.module.includes('基础')) || n.difficulty <= 2)
          const sorted = basics.length ? basics.sort((a, b) => a.difficulty - b.difficulty) : graphRes.data.nodes.sort((a, b) => a.difficulty - b.difficulty)
          return sorted[0]?.name || nextTarget
        })()
        const finalTarget = validTargets.has(nextTarget) && isBeginnerTarget ? nextTarget : fallbackTarget
        window.localStorage.setItem('eduhive.target_concept', finalTarget)
        setTargetConcept(finalTarget)
        setSelectedConcept(finalTarget)
        setSelectedNodeId(finalTarget)
        setResourceConcept(finalTarget)
        if (sessionRes.data.suggested_path?.length) setPlannedPath(sessionRes.data.suggested_path)
        setSession(sessionRes.data)
        if (['text', 'visual', 'auditory', 'kinesthetic'].includes(sessionRes.data.profile.cognitive_modality)) {
          const backendStyle = sessionRes.data.profile.cognitive_modality as 'text' | 'visual' | 'auditory' | 'kinesthetic'
          styleModeRef.current = backendStyle
          setStyleMode(backendStyle)
        }
        setGraph(graphRes.data)
        if (layoutRes?.data) setGraphLayout(layoutRes.data)
        setHealth(healthRes)
        graphApi.getPersonalPath(sessionRes.data.session_id, finalTarget)
          .then((pathRes) => {
            if (cancelled || pathRes.data.error) return
            setPersonalPath(pathRes.data)
            const backendPath = pathRes.data.path_nodes?.map((node) => node.name || node.id).filter(Boolean)
            if (backendPath?.length) setPlannedPath(backendPath)
          })
          .catch(() => undefined)
        await behaviorApi.log(sessionRes.data.session_id, 'command_center_opened', finalTarget, {
          surface: 'command-center',
        }).catch(() => undefined)
      } catch {
        if (!cancelled) {
          setResourceStatus('后端连接中断，已切换为演示数据')
        }
      }
    }

    bootstrap()
    return () => {
      cancelled = true
    }
  }, [targetConcept])

  useEffect(() => {
    if (!session) return
    const sessionId = session.session_id

    async function loadLearningSignals() {
      const [statsRes, heatmapRes, profileRes, planRes, eventsRes] = await Promise.allSettled([
        sessionApi.getStats(sessionId),
        evaluationApi.getHeatmap(sessionId),
        sessionApi.getProfile(sessionId),
        sessionApi.getLearningPlan(sessionId),
        sessionApi.getEvents(sessionId, 8),
      ])

      if (statsRes.status === 'fulfilled') setStats(statsRes.value.data)
      if (heatmapRes.status === 'fulfilled') setHeatmap(heatmapRes.value.data.data || [])
      if (profileRes.status === 'fulfilled' && !profileRes.value.data?.error) {
        setSession((current) => current && current.session_id === sessionId
          ? {
              ...current,
              profile: {
                ...current.profile,
                ...profileRes.value.data,
                cognitive_modality: styleModeRef.current,
              },
            }
          : current)
      }
      if (planRes.status === 'fulfilled') {
        setLearningPlan(planRes.value.data)
      } else {
        setLearningPlan(null)
      }
      if (eventsRes.status === 'fulfilled') {
        setLearningEvents([...(eventsRes.value.data.events || [])].sort((a, b) =>
          String(b.created_at || '').localeCompare(String(a.created_at || ''))
        ))
      }
    }

    loadLearningSignals()
    const timer = window.setInterval(loadLearningSignals, 30000)
    return () => window.clearInterval(timer)
  }, [session])

  useEffect(() => {
    if (!session) return
    const sessionId = session.session_id
    async function loadAgentTraces() {
      try {
        const res = await sessionApi.getAgentTrace(sessionId)
        setAgentTraces(res.data.traces || [])
      } catch {
        setAgentTraces([])
      }
    }
    loadAgentTraces()
    const timer = window.setInterval(loadAgentTraces, 30000)
    return () => window.clearInterval(timer)
  }, [session])

  const graphConcepts = useMemo(() => new Set(graph?.nodes.map((node) => node.name) ?? []), [graph])
  const pageTitle = NAV_ITEMS.find((item) => item.key === activeNav)?.label ?? '知识图谱'

  const pathNodes = useMemo<PathNode[]>(() => {
    const backendNodes = buildBackendPathNodes(graphLayout, personalPath, heatmap)
    return backendNodes.length ? backendNodes : buildPathNodes(graph, heatmap)
  }, [graphLayout, personalPath, graph, heatmap])
  const graphEdges = useMemo<KnowledgeEdge[]>(() => {
    const baseEdges = graphLayout?.edges?.length ? graphLayout.edges : graph?.edges.length ? graph.edges : [
    { source: 'Python 基础语法', target: '变量基础', strength: 0.8 },
    { source: '数据类型与变量', target: '变量基础', strength: 0.8 },
    { source: '输入与输出', target: '文件读写', strength: 0.8 },
    { source: '变量基础', target: '条件判断', strength: 0.8 },
    { source: '条件判断', target: '循环结构', strength: 0.8 },
    { source: '循环结构', target: '函数封装', strength: 0.8 },
    { source: '函数封装', target: '文件读写', strength: 0.8 },
    ]
    const pathMeta = new Map((personalPath?.path_edges ?? []).map((edge) => [`${edge.source}->${edge.target}`, edge]))
    const merged = baseEdges.map((edge) => ({
      ...edge,
      ...(pathMeta.get(`${edge.source}->${edge.target}`) ?? {}),
    } as KnowledgeEdge & Record<string, any>))
    for (const edge of personalPath?.path_edges ?? []) {
      if (!merged.some((item) => item.source === edge.source && item.target === edge.target)) {
        merged.push({ ...edge, strength: 1 } as KnowledgeEdge & Record<string, any>)
      }
    }
    return merged
  }, [personalPath, graphLayout, graph])

  const masteredCount = pathNodes.filter((node) => node.mastery >= 80).length
  const selectedNode = pathNodes.find((node) => node.id === selectedNodeId || node.title === selectedConcept) ?? pathNodes[pathNodes.length - 1]
  const learningGoalConcept = plannedPath[plannedPath.length - 1] || selectedConcept
  const averageMastery = selectedNode?.mastery ?? Math.round(
    pathNodes.reduce((sum, node) => sum + node.mastery, 0) / pathNodes.length
  )

  useEffect(() => {
    if (pathNodes.length === 0) return
    if (pathNodes.some((node) => node.id === selectedNodeId || node.title === selectedConcept)) return
    const nextNode = pathNodes.find((node) => /文件|操作|读写/.test(node.title)) ?? pathNodes[0]
    setSelectedNodeId(nextNode.id)
    setSelectedConcept(nextNode.title)
  }, [pathNodes, selectedConcept, selectedNodeId])

  useEffect(() => {
    if (activeNav !== 'resources') return
    loadResource(resourceConcept, 'open')
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [activeNav, resourceConcept])

  const selectNode = useCallback(async (node: PathNode) => {
    setSelectedNodeId(node.id)
    setSelectedConcept(node.title)
    setShowGraphDetail(true)
    setWorkspaceNote(`已选中知识点「${node.title}」，掌握度 ${node.mastery}%。`)
    if (session) {
      behaviorApi.log(session.session_id, 'graph_node_selected', node.title, {
        mastery: node.mastery,
        state: node.state,
      }).catch(() => undefined)
    }
    try {
      const res = await graphApi.getConcept(node.title)
      setConceptDetail(res.data)
    } catch {
      setConceptDetail(null)
    }
  }, [session])

  const closeGraphDetail = useCallback(() => setShowGraphDetail(false), [])

  const planPath = useCallback(async () => {
    navigateTo('graph', `Navigator 正在为「${selectedConcept}」规划路径...`)
    try {
      const res = session
        ? await graphApi.getPersonalPath(session.session_id, selectedConcept)
        : await graphApi.getPath(
          pathNodes.filter((node) => node.state === 'mastered').map((node) => node.title),
          selectedConcept
        )
      if (res.data.error) throw new Error(res.data.error)
      setPersonalPath(res.data)
      const nextPath = res.data.path_nodes?.map((node) => node.name || node.id).filter(Boolean)
        || (Array.isArray(res.data.path) ? res.data.path : [])
      if (!nextPath.length) throw new Error('empty path')
      setPlannedPath(nextPath)
      setWorkspaceNote(`后端知识图谱已生成路径：${nextPath.join(' → ')}`)
    } catch {
      setWorkspaceNote('路径接口暂不可用，已保留当前可视化路径。')
    }
  }, [navigateTo, session, pathNodes, selectedConcept])

  const analyzeMastery = async () => {
    if (!session) {
      setWorkspaceNote('会话尚未初始化完成，请稍后再分析掌握度。')
      return
    }
    navigateTo('progress', 'Evaluator 正在重算 BKT 掌握度...')
    setMasteryAnalyzing(true)
    try {
      const res = await evaluationApi.analyze(session.session_id)
      const recommendation = res.data.recommendation || '掌握度分析完成。'
      const weakPoints = Array.isArray(res.data.weak_points) ? res.data.weak_points : []
      const reviewPoints = Array.isArray(res.data.review_points) ? res.data.review_points : []
      const analyzedAt = new Date().toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit', second: '2-digit' })
      setWorkspaceNote(recommendation)
      setMasteryAnalysis({ weakPoints, reviewPoints, recommendation, analyzedAt })
      if (Array.isArray(res.data.heatmap_data)) {
        setHeatmap(res.data.heatmap_data)
      }
      const [heatmapRes, statsRes] = await Promise.allSettled([
        evaluationApi.getHeatmap(session.session_id),
        sessionApi.getStats(session.session_id),
      ])
      if (heatmapRes.status === 'fulfilled') setHeatmap(heatmapRes.value.data.data || [])
      if (statsRes.status === 'fulfilled') setStats(statsRes.value.data)
    } catch {
      setWorkspaceNote('评估接口暂不可用，当前展示最近一次掌握度。')
    } finally {
      setMasteryAnalyzing(false)
    }
  }

  const runCode = async () => {
    setCodeLoading(true)
    try {
      const res = await codeApi.execute(code)
      const stdout = res.data.stdout || ''
      const stderr = res.data.stderr || ''
      const violations = res.data.violations?.length ? `安全检查未通过:\n${res.data.violations.join('\n')}` : ''
      const nextOutput = (stdout + (stderr ? `\n${stderr}` : '') + (violations ? `\n${violations}` : '')).trim()
      setCodeOutput(nextOutput || '代码执行完成，无输出。')
      ;(window as any).__eduhiveLastCodeResult = res.data
      const responseVariables = extractCodeVariables(res.data)
      const nextVariables = responseVariables.length
        ? responseVariables
        : inferCodeVariables(code, nextOutput)
      setCodeVariables(nextVariables)
      if (session) {
        await behaviorApi.log(session.session_id, 'code_executed', selectedConcept, {
          source: 'command-center',
          success: res.data.success,
          variables: nextVariables.map((item) => item.name),
        }).catch(() => undefined)
      }
    } catch {
      setCodeOutput('代码执行接口暂不可用，请检查后端服务。')
      setCodeVariables([])
    } finally {
      setCodeLoading(false)
    }
  }

  const sendChat = async (messageOverride?: string, messageTypeOverride?: 'text' | 'tutor') => {
    const messageText = (typeof messageOverride === 'string' ? messageOverride : chatInput).trim()
    if (!messageText || chatLoading) return
    const wantsTutor = messageTypeOverride === 'tutor' || (!messageTypeOverride && shouldUseSocraticFallback(messageText))
    const messageType = wantsTutor ? 'tutor' : 'text'
    setChatInput('')
    const assistantId = `assistant-${Date.now()}`
    setChatMessages((prev) => [
      ...prev,
      createChatMessage('user', messageText),
      {
        ...createChatMessage('assistant', wantsTutor ? '正在连接 Socrates 辅导链路...' : '正在连接 AI 助教...', wantsTutor ? 'Socrates' : 'Agent', true),
        id: assistantId,
      },
    ])

    if (!session) {
      setChatMessages((prev) => prev.map((message) => message.id === assistantId
        ? { ...message, role: 'system', agentName: 'System', isStreaming: false, content: '后端会话还未创建完成，请稍后再发送。' }
        : message))
      return
    }

    setChatLoading(true)
    let finalResponse: AgentResponse | null = null

    const applyAssistantMessage = (content: string, agentName = 'Agent', isStreaming = true, tutorPayload?: TutorPayload) => {
      setChatMessages((prev) => prev.map((message) => message.id === assistantId
        ? { ...message, content, agentName, isStreaming, tutorPayload }
        : message))
    }
    const syncProfileFromResponse = (response: AgentResponse | null) => {
      const profile = extractProfileFromResponse(response)
      if (!profile) return
      setSession((current) => current ? {
        ...current,
        profile: {
          ...current.profile,
          ...profile,
          cognitive_modality: styleModeRef.current,
        },
      } : current)
    }
    const applyAssistantResponse = (response: AgentResponse | null, fallbackText: string) => {
      const agentText = extractAgentText(response, styleMode) || fallbackText
      const profileOnly = looksLikeProfileUpdateResponse(response)
      const tutorPayload = extractTutorPayload(response) || (
        profileOnly && wantsTutor
          ? {
              question: `我们先聚焦「${selectedConcept}」：你觉得它最核心的用途是什么？可以先用一句话说出你的理解。`,
              hint: `不要急着记定义，先想「${selectedConcept}」解决了什么学习或编程问题。`,
              canProvideAnswer: false,
              stage: 'guided',
            }
          : createSocraticFallbackPayload(agentText, selectedConcept, messageText)
      )
      const content = tutorPayload?.question || agentText
      applyAssistantMessage(content, response?.agent_name || (tutorPayload ? 'Socrates' : 'Agent'), false, tutorPayload)
    }

    try {
      const response = await sessionApi.chatStream(session.session_id, messageText, messageType)
      if (!response.ok) throw new Error(`chat-stream ${response.status}`)
      const reader = response.body?.getReader()
      if (!reader) throw new Error('无法建立 SSE 流')

      const decoder = new TextDecoder()
      let buffer = ''
      while (true) {
        const { done, value } = await reader.read()
        if (done) break
        buffer += decoder.decode(value, { stream: true })
        const chunks = buffer.split('\n\n')
        buffer = chunks.pop() || ''
        for (const chunk of chunks) {
          const dataLine = chunk.split('\n').find((line) => line.startsWith('data: '))
          if (!dataLine) continue
          const event = JSON.parse(dataLine.slice(6))
          if (event.type === 'thinking' || event.type === 'progress') {
            applyAssistantMessage(event.message || '多智能体正在协作...', event.agent || 'Agent', true)
          }
          if (event.type === 'complete') {
            finalResponse = event.agent_response as AgentResponse
            syncProfileFromResponse(finalResponse)
            applyAssistantResponse(finalResponse, '对话完成，但后端没有返回可展示文本。')
          }
          if (event.type === 'error') {
            throw new Error(event.message || 'chat-stream error')
          }
        }
      }

      if (!finalResponse) {
        const fallback = await sessionApi.chat(session.session_id, { message: messageText, message_type: messageType })
        finalResponse = fallback.data
        syncProfileFromResponse(finalResponse)
        applyAssistantResponse(finalResponse, '同步对话完成，但没有可展示文本。')
      }
    } catch (error) {
      try {
        const fallback = await sessionApi.chat(session.session_id, { message: messageText, message_type: messageType })
        finalResponse = fallback.data
        syncProfileFromResponse(finalResponse)
        applyAssistantResponse(finalResponse, '同步对话完成，但没有可展示文本。')
      } catch {
        applyAssistantMessage('后端对话接口暂不可用，请确认服务已启动。知识图谱、学习资源和代码沙箱仍可继续调试。', 'System', false)
      }
    } finally {
      setChatLoading(false)
    }
  }

  const loadResource = useCallback(async (concept = resourceConcept, surface: 'open' | 'refresh' | 'switch' = 'open') => {
    setResourceConcept(concept)
    const shouldUseCache = surface !== 'refresh'
    const cached = resourcePanelCacheRef.current.get(concept)
    if (shouldUseCache && cached) {
      applyResourceCache(concept, cached, surface)
      return cached.resource
    }
    const pending = resourcePanelPendingRef.current.get(concept)
    if (shouldUseCache && pending) {
      setWorkspaceNote(`正在复用「${concept}」资源包读取任务...`)
      const entry = await pending
      applyResourceCache(concept, entry, surface)
      return entry.resource
    }

    setResourcePanelLoading(true)
    setWorkspaceNote(`正在读取「${concept}」的学习资源包...`)
    let loadedResource: ResourceDetail | null = null
    const requestTask = (async (): Promise<ResourcePanelCacheEntry> => {
      const [latestRes, thinkingRes, versionRes, evolutionRes, feedbackStatsRes] = await Promise.allSettled([
        resourceApi.getLatest(concept),
        resourceApi.getThinkingPath(concept),
        resourceApi.getVersions(concept),
        resourceApi.getEvolution(concept),
        resourceApi.getFeedbackStats(concept),
      ])

      let resource: ResourceDetail | null = null
      if (latestRes.status === 'fulfilled') {
        resource = latestRes.value.data.resource
      }
      const status = resource ? `已载入「${concept}」资源包` : `「${concept}」暂无已生成资源，请先生成。`
      return {
        resource,
        status,
        thinkingSteps: thinkingRes.status === 'fulfilled' ? thinkingRes.value.data.steps || [] : [],
        versions: versionRes.status === 'fulfilled' ? versionRes.value.data.versions || [] : [],
        evolution: evolutionRes.status === 'fulfilled' ? evolutionRes.value.data : null,
        feedbackStats: feedbackStatsRes.status === 'fulfilled' ? feedbackStatsRes.value.data : null,
        cachedAt: Date.now(),
      }
    })()
    resourcePanelPendingRef.current.set(concept, requestTask)
    try {
      const entry = await requestTask
      loadedResource = entry.resource
      resourcePanelCacheRef.current.set(concept, entry)
      setResourcePackage(entry.resource)
      setThinkingSteps(entry.thinkingSteps)
      setVersions(entry.versions)
      setResourceEvolution(entry.evolution)
      setFeedbackStats(entry.feedbackStats)
      setResourceStatus(entry.status)
      setWorkspaceNote(entry.resource ? `已载入「${concept}」资源包` : `「${concept}」暂无已生成资源，请先生成。`)
      if (session) {
        behaviorApi.log(session.session_id, 'resource_switched', concept, { surface }).catch(() => undefined)
      }
    } catch {
      setResourceStatus('资源详情接口暂不可用')
      setWorkspaceNote('未能读取资源详情，请确认后端服务已启动。')
      setResourceEvolution(null)
      setFeedbackStats(null)
    } finally {
      resourcePanelPendingRef.current.delete(concept)
      setResourcePanelLoading(false)
    }
    return loadedResource
  }, [applyResourceCache, resourceConcept, session])

  const generateResource = useCallback(async (concept = selectedConcept, source: 'goal' | 'node' | 'resource' = 'node') => {
    if (!session) {
      setResourceStatus('会话尚未创建完成，请稍后再试。')
      setWorkspaceNote('后端会话还在初始化，资源生成需要有效 session_id。')
      return
    }
    setResourceConcept(concept)
    const sourceCopy = source === 'goal' ? '当前学习目标' : source === 'resource' ? '资源页当前知识点' : '当前节点'
    setWorkspaceNote(`正在为${sourceCopy}「${concept}」生成学习资源。`)
    setResourceLoading(true)
    setResourceStatus(`Navigator 正在规划「${concept}」资源...`)
    try {
      const response = await resourceApi.generateStream(session.session_id, concept)
      const reader = response.body?.getReader()
      if (!reader) throw new Error('无法建立资源生成流')
      const decoder = new TextDecoder()
      let buffer = ''
      let completedResource: ResourceDetail | null = null
      while (true) {
        const { done, value } = await reader.read()
        if (done) break
        buffer += decoder.decode(value, { stream: true })
        const lines = buffer.split('\n')
        buffer = lines.pop() || ''
        for (const line of lines) {
          if (!line.startsWith('data: ')) continue
          const event = JSON.parse(line.slice(6))
          if (event.message) {
            setResourceStatus(event.message)
            setWorkspaceNote(event.message)
          }
          if (event.type === 'complete') {
            completedResource = {
              concept,
              ...(event.package || {}),
              debate_report: event.debate_report || {},
              status: event.debate_report?.status === 'REJECTED' ? 'rejected' : 'approved',
            }
            setResourcePackage(completedResource)
            setResourceStatus('资源生成与辩论审核完成')
            setWorkspaceNote(`「${concept}」资源生成与辩论审核完成，可查看讲义、练习与审核记录。`)
          }
        }
      }
      if (completedResource) {
        resourcePanelCacheRef.current.delete(concept)
      }
      const loadedResource = await loadResource(concept, 'refresh').catch(() => {
        if (completedResource) {
          setResourcePackage(completedResource)
          const fallbackEntry: ResourcePanelCacheEntry = {
            resource: completedResource,
            status: '资源生成与辩论审核完成',
            thinkingSteps,
            versions,
            evolution: resourceEvolution,
            feedbackStats,
            cachedAt: Date.now(),
          }
          resourcePanelCacheRef.current.set(concept, fallbackEntry)
        }
        return completedResource
      })
      const finalResource = loadedResource || completedResource
      if (finalResource) {
        navigateTo('resources', `「${concept}」学习资源已生成，可查看讲义、练习与审核记录。`)
      } else {
        setResourceStatus(`「${concept}」资源生成未完成，请稍后重试或切换知识点。`)
        setWorkspaceNote(`「${concept}」资源生成未完成，已展示最新可用资源（如有）。`)
      }
    } catch {
      setResourceStatus('资源生成流未连接，当前展示本地演示状态')
      setWorkspaceNote('资源生成接口未连接；你仍可调试前端交互和其他接口。')
    } finally {
      setResourceLoading(false)
    }
  }, [session, selectedConcept, loadResource, thinkingSteps, versions, resourceEvolution, feedbackStats, navigateTo])

  const generateGraphResource = useCallback((concept: string) => generateResource(concept, 'node'), [generateResource])

  const sendCodeCaseToSandbox = (codeCase: Record<string, any>) => {
    const nextCode = String(codeCase.code || codeCase.starter_code || SAMPLE_CODE)
    setCode(nextCode)
    navigateTo('code', `已将「${codeCase.title || resourceConcept}」代码案例载入代码沙箱。`)
    if (session) {
      behaviorApi.log(session.session_id, 'code_case_viewed', resourceConcept, {
        title: codeCase.title,
        action: 'send_to_sandbox',
      }).catch(() => undefined)
    }
  }

  const runResourceCode = async (codeText: string) => {
    const res = await codeApi.execute(codeText)
    return res.data
  }

  const submitResourceFeedback = async (concept: string, data: { rating?: number; confusion_marked?: boolean; error_report?: string }) => {
    if (!session) throw new Error('会话未创建')
    const resourceId = resourcePackage?.resource_id || `feedback-${Date.now()}`
    await resourceApi.submitFeedback({
      session_id: session.session_id,
      resource_id: resourceId,
      concept,
      rating: data.rating,
      confusion_marked: data.confusion_marked,
      error_report: data.error_report,
    })
    resourceApi.getFeedbackStats(concept)
      .then((res) => {
        setFeedbackStats(res.data)
        const cached = resourcePanelCacheRef.current.get(concept)
        if (cached) {
          resourcePanelCacheRef.current.set(concept, {
            ...cached,
            feedbackStats: res.data,
            cachedAt: Date.now(),
          })
        }
      })
      .catch(() => undefined)
  }

  const judgeResourceExercise = async (exercise: Record<string, any>, codeText: string) => {
    const res = await codeApi.judgeExercise({
      code: codeText,
      expected_output: String(exercise.expected_output || ''),
      session_id: session?.session_id,
      concept: resourceConcept,
    })
    if (session) {
      behaviorApi.log(session.session_id, 'exercise_attempt', resourceConcept, {
        question: exercise.question,
      }).catch(() => undefined)
    }
    return res.data
  }

  const runAgentAction = async (agentName: string) => {
    if (agentName === 'Profiler') {
      navigateTo('profile', 'Profiler 已准备更新学习画像。')
      setChatInput('请根据我的学习行为更新学习画像')
      return
    }
    if (agentName === 'Navigator') {
      await planPath()
      return
    }
    if (agentName === 'Builder') {
      await generateResource(learningGoalConcept, 'goal')
      return
    }
    if (agentName === 'Reviewer') {
      navigateTo('profile', `Reviewer 正在读取「${selectedConcept}」的审核回放...`)
      setWorkspaceNote(`Reviewer 正在读取「${selectedConcept}」的审核回放...`)
      try {
        const [thinkingRes, versionRes] = await Promise.all([
          resourceApi.getThinkingPath(selectedConcept),
          resourceApi.getVersions(selectedConcept),
        ])
        setThinkingSteps(thinkingRes.data.steps || [])
        setVersions(versionRes.data.versions || [])
        setWorkspaceNote('审核回放与版本演进已更新。')
      } catch {
        setWorkspaceNote('审核/版本接口暂无记录，先生成一次资源即可看到回放。')
      }
      return
    }
    navigateTo('chat', 'Socrates 已准备辅导问题，点击对话发送即可触发。')
    setChatInput(`我在学习「${selectedConcept}」时答错了，请用苏格拉底方式引导我`)
  }

  const selectHeatCell = async (cell: SelectedHeatCell) => {
    setSelectedHeatCell(cell)
    navigateTo('progress', `已选中「${cell.concept || `${cell.column}/${cell.row}`}」，当前掌握度 ${cell.value}%。`)
    if (session) {
      behaviorApi.log(session.session_id, 'heatmap_cell_selected', cell.concept || cell.column, {
        row: cell.row,
        column: cell.column,
        value: cell.value,
        observations: cell.observations,
      }).catch(() => undefined)
      if (cell.concept) {
        setBktLoading(true)
        try {
          const res = await evaluationApi.getBkt(session.session_id, cell.concept)
          setBktDetail(res.data)
        } catch {
          setBktDetail(null)
          setWorkspaceNote('已选中热力图单元，但 BKT 详情接口暂不可用。')
        } finally {
          setBktLoading(false)
        }
      }
    }
  }

  const changeStyleMode = async (mode: 'text' | 'visual' | 'auditory' | 'kinesthetic') => {
    styleModeRef.current = mode
    setStyleMode(mode)
    setSession((current) => current ? {
      ...current,
      profile: {
        ...current.profile,
        cognitive_modality: mode,
      },
    } : current)
    const modeLabel = mode === 'text' ? '文字型' : mode === 'visual' ? '视觉型' : mode === 'auditory' ? '听觉型' : '动觉型'
    setWorkspaceNote(`认知风格画像已切换为：${modeLabel}。`)
    if (session) {
      sessionApi.updateProfile(session.session_id, { cognitive_modality: mode })
        .then((res) => {
          if (res.data.profile) {
            mergeSessionProfile(res.data.profile)
          }
        })
        .catch(() => {
          setWorkspaceNote('认知风格已在前端切换，但后端画像同步失败，请确认服务状态。')
        })
      behaviorApi.log(session.session_id, 'cognitive_style_preview', selectedConcept, {
        mode,
        description: `用户手动切换认知风格为 ${mode}`,
      }).catch(() => undefined)
    }
  }

  const portalCourses = useMemo(() => [
    COURSE_CATALOG[0],
    ...publishedCourseCards,
    ...COURSE_CATALOG.slice(1),
  ], [publishedCourseCards])
  const selectedCourse = portalCourses.find((course) => course.id === selectedCourseId) ?? portalCourses[0]

  if (courseMode === 'portal') {
    return (
      <CoursePortal
        courses={portalCourses}
        onOpenCourse={openCourse}
        authUser={authUser}
        authRole={authRole}
        loginRole={loginRole}
        loginUsername={loginUsername}
        loginPassword={loginPassword}
        loginMode={loginMode}
        loginStatus={loginStatus}
        authLoading={authLoading}
        onUsernameChange={setLoginUsername}
        onLoginRoleChange={setLoginRole}
        onPasswordChange={setLoginPassword}
        onLoginModeChange={setLoginMode}
        onSubmitAuth={submitPortalAuth}
        onLogout={logoutPortal}
      />
    )
  }

  if (courseMode === 'teacher') {
    return <TeacherWorkspace onBack={openPortal} onLogout={logoutPortal} />
  }

  if (courseMode === 'admin') {
    return <AdminWorkspace onBack={openPortal} onLogout={logoutPortal} />
  }

  if (courseMode === 'empty') {
    return <EmptyCoursePage course={selectedCourse} onBack={openPortal} />
  }

  return (
    <div className={cn('command-shell min-h-screen text-slate-100', `style-mode-${styleMode}`)}>
      <HexBackdrop />
      <aside className="command-sidebar">
        <BrandBlock />
        <button type="button" onClick={openPortal} className="course-back-link">
          <Home className="h-4 w-4" />
          课程广场
        </button>
        <nav className="mt-10 space-y-3">
          {NAV_ITEMS.map((item) => (
            <button
              key={item.key}
              onClick={() => navigateTo(item.key)}
              className={cn('side-nav-item', activeNav === item.key && 'side-nav-item-active')}
            >
              <item.icon className="h-5 w-5" />
              <span>{item.label}</span>
            </button>
          ))}
        </nav>

        <div className="mt-auto space-y-4">
          <LearningMeter stats={stats} />
          <StreakCard stats={stats} />
        </div>
      </aside>

      <main className="relative min-h-screen pl-0 lg:pl-[250px]">
        <div className="mx-auto flex min-h-screen max-w-[1780px] flex-col gap-3 p-3 sm:p-5">
          <TopBar
            sessionId={session?.session_id}
            health={health}
            pageTitle={pageTitle}
            resourceStatus={resourceStatus}
            learningGoalConcept={learningGoalConcept}
            onGenerateResource={() => generateResource(learningGoalConcept, 'goal')}
            resourceLoading={resourceLoading}
          />

          <CourseStudyHeader
            course={COURSE_CATALOG[0]}
            activeNav={activeNav}
            selectedConcept={selectedConcept}
            masteredCount={masteredCount}
            totalConcepts={graphConcepts.size}
            averageMastery={averageMastery}
            onBack={openPortal}
            onNavigate={navigateTo}
          />

          <section className="module-page flex-1">
            {activeNav === 'profile' && (
              <div className="module-grid profile-page">
                <ProfilePanel session={session} masteredCount={masteredCount} targetConcept={targetConcept} stats={stats} totalConcepts={graphConcepts.size} />
                <AgentPanel onAgentAction={runAgentAction} traces={agentTraces} />
                <WorkspaceDock
                  activeNav={activeNav}
                  selectedConcept={selectedConcept}
                  styleMode={styleMode}
                  workspaceNote={workspaceNote}
                  thinkingSteps={thinkingSteps}
                  versions={versions}
                  learningPlan={learningPlan}
                  learningEvents={learningEvents}
                  onStyleChange={changeStyleMode}
                  onAnalyze={analyzeMastery}
                  onPlanPath={planPath}
                />
              </div>
            )}

            {activeNav === 'graph' && (
              <div className={cn('module-grid graph-page', showGraphDetail && 'graph-page-detailing')}>
                <KnowledgePanel
                  nodes={pathNodes}
                  edges={graphEdges}
                  plannedPath={plannedPath}
                  selectedNodeId={selectedNodeId}
                  selectedConcept={selectedConcept}
                  graphConcepts={graphConcepts}
                  averageMastery={averageMastery}
                  resourceStatus={resourceStatus}
                  conceptDetail={conceptDetail}
                  showDetail={showGraphDetail}
                  focusNonce={graphFocusNonce}
                  onNodeSelect={selectNode}
                  onCanvasBlankClick={closeGraphDetail}
                  onPlanPath={planPath}
                  onGenerateResource={generateGraphResource}
                />
                <WorkspaceDock
                  activeNav={activeNav}
                  selectedConcept={selectedConcept}
                  styleMode={styleMode}
                  workspaceNote={workspaceNote}
                  thinkingSteps={thinkingSteps}
                  versions={versions}
                  learningPlan={learningPlan}
                  learningEvents={learningEvents}
                  onStyleChange={changeStyleMode}
                  onAnalyze={analyzeMastery}
                  onPlanPath={planPath}
                />
              </div>
            )}

            {activeNav === 'resources' && (
              <div className="module-grid resource-page">
                <ResourceLibraryPanel
                  selectedConcept={resourceConcept}
                  resource={resourcePackage}
                  resourceStatus={resourceStatus}
                  loading={resourcePanelLoading}
                  versions={versions}
                  evolution={resourceEvolution}
                  feedbackStats={feedbackStats}
                  thinkingSteps={thinkingSteps}
                  styleMode={styleMode}
                  onStyleChange={changeStyleMode}
                  onGenerateResource={() => generateResource(resourceConcept, 'resource')}
                  onRefresh={() => loadResource(resourceConcept, 'refresh')}
                  onPlanPath={planPath}
                  onSendCodeCase={sendCodeCaseToSandbox}
                  onRunCode={runResourceCode}
                  onJudgeExercise={judgeResourceExercise}
                  onSectionView={(section) => {
                    if (session) {
                      behaviorApi.log(session.session_id, section === 'mindmap' ? 'mindmap_clicked' : section === 'review' ? 'debate_viewed' : 'resource_switched', resourceConcept, {
                        section,
                      }).catch(() => undefined)
                    }
                  }}
                  onSubmitFeedback={(data) => submitResourceFeedback(resourceConcept, data)}
                />
                <WorkspaceDock
                  activeNav={activeNav}
                  selectedConcept={selectedConcept}
                  styleMode={styleMode}
                  workspaceNote={workspaceNote}
                  thinkingSteps={thinkingSteps}
                  versions={versions}
                  learningPlan={learningPlan}
                  learningEvents={learningEvents}
                  onStyleChange={changeStyleMode}
                  onAnalyze={analyzeMastery}
                  onPlanPath={planPath}
                />
              </div>
            )}

            {activeNav === 'chat' && (
              <div className="module-grid chat-page">
                <ChatCommand
                  input={chatInput}
                  setInput={setChatInput}
                  messages={chatMessages}
                  loading={chatLoading}
                  targetConcept={selectedConcept}
                  onSend={sendChat}
                  onContinueTutor={() => sendChat(`我对「${selectedConcept}」还没有想清楚，请继续用一个具体问题引导我。`, 'tutor')}
                />
                <WorkspaceDock
                  activeNav={activeNav}
                  selectedConcept={selectedConcept}
                  styleMode={styleMode}
                  workspaceNote={workspaceNote}
                  thinkingSteps={thinkingSteps}
                  versions={versions}
                  learningPlan={learningPlan}
                  learningEvents={learningEvents}
                  onStyleChange={changeStyleMode}
                  onAnalyze={analyzeMastery}
                  onPlanPath={planPath}
                />
              </div>
            )}

            {activeNav === 'code' && (
              <div className="module-grid code-page">
                <CodeCommand
                  code={code}
                  setCode={setCode}
                  output={codeOutput}
                  variables={codeVariables}
                  loading={codeLoading}
                  onRun={runCode}
                  onReset={() => {
                    setCode(SAMPLE_CODE)
                    setCodeOutput(SAMPLE_OUTPUT)
                    setCodeVariables(SAMPLE_VARIABLES)
                  }}
                />
                <WorkspaceDock
                  activeNav={activeNav}
                  selectedConcept={selectedConcept}
                  styleMode={styleMode}
                  workspaceNote={workspaceNote}
                  thinkingSteps={thinkingSteps}
                  versions={versions}
                  learningPlan={learningPlan}
                  learningEvents={learningEvents}
                  onStyleChange={changeStyleMode}
                  onAnalyze={analyzeMastery}
                  onPlanPath={planPath}
                />
              </div>
            )}

            {activeNav === 'progress' && (
              <div className="module-grid progress-page">
                <HeatmapPanel
                  items={heatmap}
                  stats={stats}
                  selectedCell={selectedHeatCell}
                  bktDetail={bktDetail}
                  bktLoading={bktLoading}
                  analyzing={masteryAnalyzing}
                  analysis={masteryAnalysis}
                  onSelectCell={selectHeatCell}
                  onAnalyze={analyzeMastery}
                />
                <WorkspaceDock
                  activeNav={activeNav}
                  selectedConcept={selectedConcept}
                  styleMode={styleMode}
                  workspaceNote={workspaceNote}
                  thinkingSteps={thinkingSteps}
                  versions={versions}
                  learningPlan={learningPlan}
                  learningEvents={learningEvents}
                  onStyleChange={changeStyleMode}
                  onAnalyze={analyzeMastery}
                  onPlanPath={planPath}
                />
              </div>
            )}
          </section>
        </div>
      </main>
      <FloatingAssistant activeNav={activeNav} selectedConcept={selectedConcept} />
    </div>
  )
}

type CoursePortalProps = {
  courses: CourseCard[]
  onOpenCourse: (course: CourseCard) => void
  authUser: string
  authRole: UserRole
  loginRole: UserRole
  loginUsername: string
  loginPassword: string
  loginMode: 'login' | 'register'
  loginStatus: string
  authLoading: boolean
  onUsernameChange: (value: string) => void
  onLoginRoleChange: (value: UserRole) => void
  onPasswordChange: (value: string) => void
  onLoginModeChange: (value: 'login' | 'register') => void
  onSubmitAuth: (continueCourse?: CourseCard) => void
  onLogout: () => void
}

function CoursePortal({
  courses,
  onOpenCourse,
  authUser,
  authRole,
  loginRole,
  loginUsername,
  loginPassword,
  loginMode,
  loginStatus,
  authLoading,
  onUsernameChange,
  onLoginRoleChange,
  onPasswordChange,
  onLoginModeChange,
  onSubmitAuth,
  onLogout,
}: CoursePortalProps) {
  const featured = courses[0]
  const activePortalRole = authUser ? authRole : loginRole
  const roleLabel = activePortalRole === 'teacher' ? '教师' : activePortalRole === 'admin' ? '管理员' : '学生'
  const roleHomeLabel = activePortalRole === 'teacher' ? '进入教师工作台' : activePortalRole === 'admin' ? '进入管理后台' : '继续学习'
  const accountPanelTitle = authUser
    ? (activePortalRole === 'student' ? '学习账户' : `${roleLabel}账户`)
    : (loginMode === 'register' ? `创建${roleLabel}账户` : `${roleLabel}登录`)
  const portalCopy = {
    student: {
      kicker: 'AI 驱动的个性化课程空间',
      title: ['选择课程', '进入你的智学蜂巢'],
      summary: '从目标出发，系统会结合你的学习记录与掌握情况，推荐更适合当前阶段的课程内容。',
      primary: '进入推荐课程',
      secondary: authUser ? '查看学习账户' : '登录后同步学习记录',
      steps: [
        ['选课', '从课程广场进入', BookOpen],
        ['规划', '生成学习路径', Route],
        ['学习', '对话与资源协同', MessageSquare],
        ['评估', '追踪掌握进度', BarChart3],
      ],
    },
    teacher: {
      kicker: '教师课程建设空间',
      title: ['管理课程', '组织你的教学内容'],
      summary: '教师端聚焦课程创建、资料上传和课程状态维护。登录后进入教师工作台处理自己的课程。',
      primary: authUser ? '进入教师工作台' : '教师登录',
      secondary: '查看课程目录',
      steps: [
        ['建课', '创建课程信息', BookOpen],
        ['整理', '维护课程状态', Layers3],
        ['发布', '开放学习入口', ShieldCheck],
        ['复盘', '查看真实记录', BarChart3],
      ],
    },
    admin: {
      kicker: '平台管理中心',
      title: ['管理平台', '维护课程与账号'],
      summary: '管理端聚焦用户、课程和平台运行概览。登录管理员账号后进入后台处理基础数据。',
      primary: authUser ? '进入管理后台' : '管理员登录',
      secondary: '查看课程目录',
      steps: [
        ['账号', '查看用户角色', UserRound],
        ['课程', '管理课程状态', Layers3],
        ['统计', '读取真实数据', BarChart3],
        ['权限', '控制后台访问', ShieldCheck],
      ],
    },
  }[activePortalRole]
  const categories = ['全部课程', ...Array.from(new Set(courses.map((course) => course.category)))]
  const [activeCategory, setActiveCategory] = useState('全部课程')
  const [courseQuery, setCourseQuery] = useState('')
  const [loginCardPulse, setLoginCardPulse] = useState(false)
  const loginCardRef = useRef<HTMLFormElement | null>(null)
  const coursesRef = useRef<HTMLElement | null>(null)
  const filteredCourses = useMemo(() => {
    const keyword = courseQuery.trim().toLowerCase()
    return courses.filter((course) => {
      const matchesCategory = activeCategory === '全部课程' || course.category === activeCategory
      const searchPool = [course.title, course.category, course.level, course.teacher, course.summary, ...course.tags]
        .join(' ')
        .toLowerCase()
      return matchesCategory && (!keyword || searchPool.includes(keyword))
    })
  }, [activeCategory, courseQuery, courses])

  const focusLoginCard = () => {
    loginCardRef.current?.scrollIntoView({ behavior: 'smooth', block: 'center' })
    setLoginCardPulse(true)
    window.setTimeout(() => setLoginCardPulse(false), 900)
    if (!authUser) {
      window.setTimeout(() => {
        loginCardRef.current?.querySelector<HTMLInputElement>('input[name="portal-username"]')?.focus()
      }, 280)
    }
  }

  const showCourseResults = () => {
    coursesRef.current?.scrollIntoView({ behavior: 'smooth', block: 'start' })
  }

  const openRoleHome = () => {
    if (activePortalRole === 'teacher') {
      window.location.hash = '/teacher'
      return
    }
    if (activePortalRole === 'admin') {
      window.location.hash = '/admin'
      return
    }
    onOpenCourse(featured)
  }

  return (
    <div className="course-portal min-h-screen">
      <header className="portal-nav">
        <BrandBlock />
        <nav>
          {categories.map((category) => (
            <button
              key={category}
              type="button"
              className={activeCategory === category ? 'active' : ''}
              aria-pressed={activeCategory === category}
              onClick={() => {
                setActiveCategory(category)
                coursesRef.current?.scrollIntoView({ behavior: 'smooth', block: 'start' })
              }}
            >
              {category}
            </button>
          ))}
        </nav>
        <div className="portal-login">
          <button type="button" className="portal-login-status" onClick={focusLoginCard}>
            <Mail className="h-4 w-4" /> {authUser || '未登录'}
          </button>
          <button type="button" onClick={authUser ? onLogout : focusLoginCard} disabled={authLoading}>
            <LockKeyhole className="h-4 w-4" /> {authUser ? '退出登录' : '登录'}
          </button>
        </div>
      </header>

      <main className="portal-main">
        <section className="portal-hero">
          <div className="portal-hero-copy">
            <p className="portal-kicker">{portalCopy.kicker}</p>
            <h1><span>{portalCopy.title[0]}</span><span>{portalCopy.title[1]}</span></h1>
            <span>{portalCopy.summary}</span>
            <div className="portal-hero-chips" aria-label="平台能力">
              <span><Sparkles className="h-3.5 w-3.5" /> 智能辅助</span>
              <span><Network className="h-3.5 w-3.5" /> 多端协同</span>
              <span><Brain className="h-3.5 w-3.5" /> 真实数据</span>
            </div>
            <div className="portal-search">
              <Search className="h-5 w-5" />
              <input
                value={courseQuery}
                onChange={(event) => setCourseQuery(event.target.value)}
                onKeyDown={(event) => {
                  if (event.key === 'Enter') showCourseResults()
                }}
                placeholder="搜索 Python 文件读写、数据结构、AI 通识"
                aria-label="课程搜索"
              />
              <button type="button" onClick={showCourseResults}>搜索课程</button>
            </div>
            <div className="portal-hero-actions">
              <button type="button" className="portal-primary-action" onClick={authUser ? openRoleHome : focusLoginCard}>
                {portalCopy.primary} <ChevronRight className="h-4 w-4" />
              </button>
              <button type="button" className="portal-ghost-action" onClick={activePortalRole === 'student' ? focusLoginCard : showCourseResults}>
                {portalCopy.secondary}
              </button>
            </div>
            <div className="portal-learning-flow" aria-label="学习流程">
              {portalCopy.steps.map(([title, desc, Icon], index) => (
                <Fragment key={title as string}>
                  {index > 0 && <i />}
                  <div>
                    <span><Icon className="h-4 w-4" /></span>
                    <strong>{title as string}</strong>
                    <em>{desc as string}</em>
                  </div>
                </Fragment>
              ))}
            </div>
          </div>
          <div className="portal-hero-side">
            <PortalDigitalHuman
              authUser={authUser}
              activeRole={activePortalRole}
              onFocusLogin={focusLoginCard}
              onShowCourses={showCourseResults}
              onOpenRoleHome={openRoleHome}
            />
            <form ref={loginCardRef} className={cn('portal-login-card', loginCardPulse && 'is-attention')} onSubmit={(event) => {
              event.preventDefault()
              onSubmitAuth()
            }}>
              <strong>{accountPanelTitle}</strong>
              {authUser ? (
                <>
                  <div className="portal-account-panel">
                    <span>当前账号</span>
                    <b>{authUser}</b>
                    <small>身份：{roleLabel}</small>
                  </div>
                  <button type="button" onClick={openRoleHome}>{roleHomeLabel}</button>
                  <button type="button" className="portal-secondary-button" onClick={onLogout} disabled={authLoading}>退出登录</button>
                </>
              ) : (
                <>
                  <div className="portal-login-tabs" role="group" aria-label="登录模式">
                    <button type="button" className={loginMode === 'login' ? 'active' : ''} onClick={() => onLoginModeChange('login')}>登录</button>
                    <button type="button" className={loginMode === 'register' ? 'active' : ''} onClick={() => onLoginModeChange('register')}>注册</button>
                  </div>
                  <div className="portal-login-tabs role-login-tabs" role="group" aria-label="用户身份">
                    {[
                      ['student', '学生'],
                      ['teacher', '教师'],
                      ['admin', '管理员'],
                    ].map(([role, label]) => (
                      <button
                        key={role}
                        type="button"
                        className={loginRole === role ? 'active' : ''}
                        onClick={() => onLoginRoleChange(role as UserRole)}
                      >
                        {label}
                      </button>
                    ))}
                  </div>
                  <label>
                    <span>账号</span>
                    <input name="portal-username" value={loginUsername} onChange={(event) => onUsernameChange(event.target.value)} placeholder="请输入用户名或邮箱" autoComplete="username" />
                  </label>
                  <label>
                    <span>密码</span>
                    <input value={loginPassword} onChange={(event) => onPasswordChange(event.target.value)} placeholder="请输入密码" type="password" autoComplete={loginMode === 'register' ? 'new-password' : 'current-password'} />
                  </label>
                  <button type="submit" disabled={authLoading}>
                    {authLoading ? '处理中...' : loginMode === 'register' ? '注册' : '登录'}
                  </button>
                </>
              )}
              <p>{loginStatus}</p>
            </form>
          </div>
        </section>

        <section className="portal-section" ref={coursesRef}>
          <div className="portal-section-title">
            <div>
              <p>课程中心</p>
              <h2>{activeCategory === '全部课程' ? '推荐课程' : activeCategory}</h2>
            </div>
            <span>{filteredCourses.length ? `已为你筛选出 ${filteredCourses.length} 门课程。开放课程可直接进入学习，建设中的课程会持续更新。` : '没有找到匹配课程，可以切换分类或修改关键词。'}</span>
          </div>
          <div className="course-card-grid">
            {filteredCourses.map((course) => (
              <button key={course.id} type="button" onClick={() => onOpenCourse(course)} className={cn('course-card', `course-card-${course.accent}`)}>
                <div className="course-card-cover">
                  <BookOpen className="h-7 w-7" />
                  <span>{course.workspace === 'materials' ? '可查看资料' : course.status === 'ready' ? '已开放' : '建设中'}</span>
                </div>
                <div className="course-card-body">
                  <p>{course.category} · {course.level}</p>
                  <h3>{course.title}</h3>
                  <span>{course.summary}</span>
                  <div className="course-card-meta">
                    <em><UserRound className="h-3.5 w-3.5" />{course.teacher}</em>
                    <em><Clock3 className="h-3.5 w-3.5" />{course.duration}</em>
                  </div>
                  <div className="course-card-tags">
                    {course.tags.map((tag) => <i key={tag}>{tag}</i>)}
                  </div>
                </div>
                <strong>{course.workspace === 'materials' ? '查看资料' : course.status === 'ready' ? '进入课程' : '查看状态'}<ChevronRight className="h-4 w-4" /></strong>
              </button>
            ))}
            {!filteredCourses.length && (
              <div className="course-empty-result">
                <Search className="h-6 w-6" />
                <strong>暂无匹配课程</strong>
                <span>试试“Python”“AI”或切换到全部课程。</span>
              </div>
            )}
          </div>
        </section>
      </main>
    </div>
  )
}

function PortalDigitalHuman({
  authUser,
  activeRole,
  onFocusLogin,
  onShowCourses,
  onOpenRoleHome,
}: {
  authUser: string
  activeRole: UserRole
  onFocusLogin: () => void
  onShowCourses: () => void
  onOpenRoleHome: () => void
}) {
  const { speaking, source, speak, stop } = useSparkTTS()
  const [imageReady, setImageReady] = useState(true)
  const [assistantGender, setAssistantGender] = useState<'male' | 'female'>('male')
  const assistantImage =
    assistantGender === 'male'
      ? '/assets/eduhive-portal-assistant-cutout.png'
      : '/assets/eduhive-portal-assistant-female-cutout.png'
  const assistantVoice = assistantGender === 'male' ? 'aisjiuxu' : 'aisjinger'
  const assistantRoleCopy: Record<UserRole, {
    title: string
    body: string
    guide: string
    coursesLabel: string
    accountLabel: string
    homeLabel: string
  }> = {
    student: {
      title: authUser ? '我可以帮你继续学习' : `你好，我是${assistantGender === 'male' ? '小蜂导学助教' : '小蜂导学学姐'}`,
      body: authUser ? '我可以带你回到已开放课程，也可以帮你重新筛选适合当前阶段的课程。' : '先选择课程，再进入对应学习工作台；登录后可以保留进度和学习记录。',
      guide: authUser
        ? `欢迎回来，${authUser}。我可以帮你继续学习已开放课程，也可以带你查看课程列表。`
        : '欢迎来到智学蜂巢课程广场。我可以帮你筛选课程、说明学习路径，并在登录后同步你的学习记录与课程进度。',
      coursesLabel: '找课程',
      accountLabel: authUser ? '账户' : '登录',
      homeLabel: '继续学习',
    },
    teacher: {
      title: authUser ? '我可以协助你管理课程' : '这里是教师登录入口',
      body: authUser ? '进入教师工作台后，可以创建课程、上传课程资料，并维护课程发布状态。' : '请选择教师身份登录，登录后进入课程建设与课程管理工作台。',
      guide: authUser
        ? `欢迎回来，${authUser}。当前是教师端，我可以带你进入教师工作台，处理课程创建、资料上传和课程状态管理。`
        : '当前是教师入口。教师登录后可以进入课程工作台，创建课程并维护课程资料。',
      coursesLabel: '课程目录',
      accountLabel: authUser ? '教师账号' : '教师登录',
      homeLabel: authUser ? '教师工作台' : '教师登录',
    },
    admin: {
      title: authUser ? '我可以协助你管理平台' : '这里是管理员登录入口',
      body: authUser ? '进入管理后台后，可以查看用户、课程和平台统计，并维护课程状态。' : '请选择管理员身份登录，登录后进入平台数据与权限管理后台。',
      guide: authUser
        ? `欢迎回来，${authUser}。当前是管理端，我可以带你进入管理后台，查看用户、课程和平台统计。`
        : '当前是管理员入口。管理员登录后可以进入后台，查看平台真实数据并管理课程状态。',
      coursesLabel: '课程目录',
      accountLabel: authUser ? '管理员账号' : '管理员登录',
      homeLabel: authUser ? '管理后台' : '管理员登录',
    },
  }
  const activeAssistantCopy = assistantRoleCopy[activeRole]
  const guideText = activeAssistantCopy.guide

  const toggleGuideVoice = () => {
    if (speaking) {
      stop()
      return
    }
    console.log('[EduHive digital human voice]', {
      scope: 'course-portal',
      assistant: assistantGender === 'male' ? '小蜂导学助教' : '小蜂导学学姐',
      gender: assistantGender,
      voice: assistantVoice,
      source,
    })
    speak(guideText, 50, assistantGender, assistantVoice)
  }

  const changeAssistantGender = (gender: 'male' | 'female') => {
    if (speaking) stop()
    setAssistantGender(gender)
    setImageReady(true)
  }

  return (
    <section className="portal-digital-human-card" aria-label="数字人导学">
      <div className="portal-digital-human-portrait">
        {imageReady ? (
          <img
            src={assistantImage}
            alt={assistantGender === 'male' ? '智学蜂巢男数字人导学助教' : '智学蜂巢女数字人导学助教'}
            draggable={false}
            onError={() => setImageReady(false)}
          />
        ) : (
          <div className="portal-digital-human-fallback" aria-hidden="true">
            <span className="fallback-head" />
            <span className="fallback-body" />
            <span className="fallback-core"><Bot className="h-5 w-5" /></span>
          </div>
        )}
        <i className={cn(speaking && 'active')} />
      </div>
      <div className="portal-digital-human-panel">
        <div className="portal-digital-human-title">
          <span><Sparkles className="h-3.5 w-3.5" /> 数字人导学</span>
          <em>{source === 'iflytek' ? '讯飞语音在线' : source === 'browser' ? '浏览器语音' : '语音检测中'}</em>
        </div>
        <strong>{activeAssistantCopy.title}</strong>
        <p>{activeAssistantCopy.body}</p>
        <div className="portal-digital-human-actions">
          <button type="button" onClick={toggleGuideVoice} className={cn(speaking && 'active')}>
            <Volume2 className="h-3.5 w-3.5" /> {speaking ? '停止导学' : '听导学'}
          </button>
          <button type="button" onClick={onShowCourses}>{activeAssistantCopy.coursesLabel}</button>
          <button type="button" onClick={onFocusLogin}>{activeAssistantCopy.accountLabel}</button>
          <button type="button" onClick={authUser ? onOpenRoleHome : onFocusLogin}>{activeAssistantCopy.homeLabel}</button>
        </div>
        <div className="portal-voice-toggle" role="group" aria-label="数字人形象">
          <span>形象</span>
          <button type="button" className={assistantGender === 'male' ? 'active' : ''} onClick={() => changeAssistantGender('male')}>男生</button>
          <button type="button" className={assistantGender === 'female' ? 'active' : ''} onClick={() => changeAssistantGender('female')}>女生</button>
        </div>
      </div>
    </section>
  )
}

function EmptyCoursePage({ course, onBack }: { course: CourseCard; onBack: () => void }) {
  const [materials, setMaterials] = useState<CourseMaterial[]>([])
  const [loadingMaterials, setLoadingMaterials] = useState(false)
  const isMaterialCourse = course.workspace === 'materials' && Boolean(course.backendCourseId)

  useEffect(() => {
    if (!isMaterialCourse || !course.backendCourseId) {
      setMaterials([])
      return
    }
    let cancelled = false
    setLoadingMaterials(true)
    teacherApi.getPublicCourseMaterials(course.backendCourseId)
      .then((res) => {
        if (!cancelled) setMaterials(res.data.materials)
      })
      .catch(() => {
        if (!cancelled) setMaterials([])
      })
      .finally(() => {
        if (!cancelled) setLoadingMaterials(false)
      })
    return () => {
      cancelled = true
    }
  }, [course.backendCourseId, isMaterialCourse])

  return (
    <div className="empty-course-page min-h-screen">
      <header className="portal-nav">
        <BrandBlock />
        <button type="button" onClick={onBack} className="portal-back-button"><Home className="h-4 w-4" /> 返回课程广场</button>
      </header>
      <main className="empty-course-main">
        <div className={cn('empty-course-card', `course-card-${course.accent}`)}>
          <div className="course-card-cover">
            <BookOpen className="h-8 w-8" />
            <span>{isMaterialCourse ? '已发布' : '建设中'}</span>
          </div>
          <p>{course.category} · {course.level}</p>
          <h1>{course.title}</h1>
          <span>{course.summary}</span>
          {isMaterialCourse ? (
            <section className="student-material-panel">
              <div className="student-material-title">
                <div>
                  <p>课程资料</p>
                  <strong>{materials.length ? `${materials.length} 个文件` : '等待资料'}</strong>
                </div>
                <span>{loadingMaterials ? '正在载入...' : '由教师维护，可下载后学习'}</span>
              </div>
              {materials.length ? (
                <div className="student-material-list">
                  {materials.map((material) => (
                    <article key={material.material_id}>
                      <FileUp className="h-4 w-4" />
                      <div>
                        <strong>{material.original_filename}</strong>
                        <span>{formatFileSize(material.file_size)} · {material.created_at.slice(0, 10)}</span>
                      </div>
                      <a href={teacherApi.downloadCourseMaterialUrl(material.material_id, true)} target="_blank" rel="noreferrer">
                        <Download className="h-3.5 w-3.5" /> 下载
                      </a>
                    </article>
                  ))}
                </div>
              ) : (
                <div className="student-material-empty">
                  {loadingMaterials ? '正在整理课程资料...' : '教师暂未添加资料。'}
                </div>
              )}
              <button type="button" onClick={onBack}>返回课程广场</button>
            </section>
          ) : (
            <>
              <strong>暂无课程内容哦~</strong>
              <button type="button" onClick={onBack}>去选择已开放课程</button>
            </>
          )}
        </div>
      </main>
    </div>
  )
}

function CourseStudyHeader({
  course,
  activeNav,
  selectedConcept,
  masteredCount,
  totalConcepts,
  averageMastery,
  onBack,
  onNavigate,
}: {
  course: CourseCard
  activeNav: NavKey
  selectedConcept: string
  masteredCount: number
  totalConcepts: number
  averageMastery: number
  onBack: () => void
  onNavigate: (nav: NavKey) => void
}) {
  const activeItem = NAV_ITEMS.find((item) => item.key === activeNav) ?? NAV_ITEMS[0]
  const moduleDescriptions: Record<NavKey, string> = {
    profile: '查看画像与协作状态',
    graph: '规划知识路径',
    resources: '学习讲义与练习',
    chat: '向 AI 助教提问',
    code: '运行 Python 代码',
    progress: '复盘掌握度变化',
  }
  const statCards = [
    { label: '学习模块', value: NAV_ITEMS.length, unit: '个', icon: Layers3 },
    { label: '知识节点', value: totalConcepts || '待载入', unit: totalConcepts ? '个' : '', icon: Network },
    { label: '已掌握', value: masteredCount, unit: '个', icon: Brain },
    { label: '平均掌握', value: `${averageMastery}%`, unit: '', icon: BarChart3 },
  ]

  return (
    <div className="course-study-header">
      <div className="course-cover-main">
        <button type="button" onClick={onBack} className="course-back-button"><Home className="h-4 w-4" /> 课程广场</button>
        <p>{course.category} · {course.level}</p>
        <div className="course-cover-title-row">
          <h2>{course.title}</h2>
          <em>智慧课程</em>
        </div>
        <span>{course.summary}</span>
        <div className="course-cover-tags">
          <strong>{course.teacher}</strong>
          <i>{course.duration}</i>
          {course.tags.map((tag) => <i key={tag}>{tag}</i>)}
        </div>
      </div>

      <div className="course-cover-system">
        <div className="course-system-title">
          <span>课程学习面板</span>
          <strong>当前模块和进度会随你的学习记录更新</strong>
        </div>
        <div className="course-current-goal">
          <activeItem.icon className="h-5 w-5" />
          <div>
            <span>当前学习空间</span>
            <strong>{activeItem.label}</strong>
          </div>
        </div>
        <div className="course-goal-pill">
          <Route className="h-4 w-4" />
          <span>目标：{selectedConcept}</span>
        </div>
        <div className="course-stat-stack">
          {statCards.map((item) => (
            <div key={item.label}>
              <item.icon className="h-4 w-4" />
              <span>{item.label}</span>
              <strong>{item.value}<small>{item.unit}</small></strong>
            </div>
          ))}
        </div>
      </div>

      <nav className="course-cover-tabs">
        {NAV_ITEMS.map((item) => (
          <button key={item.key} type="button" onClick={() => onNavigate(item.key)} className={cn(activeNav === item.key && 'active')}>
            <item.icon className="h-4 w-4" />
            <span>
              <strong>{item.label}</strong>
              <small>{moduleDescriptions[item.key]}</small>
            </span>
          </button>
        ))}
      </nav>
      <span className="course-study-tip"><Star className="h-4 w-4" /> 当前正在学习「{selectedConcept}」，你可以在{activeItem.label}中继续推进。</span>
    </div>
  )
}

function HexBackdrop() {
  return (
    <div aria-hidden="true" className="pointer-events-none fixed inset-0 overflow-hidden">
      <div className="command-bg-layer absolute inset-0" />
      <div className="absolute inset-0 opacity-[0.10] [background-image:linear-gradient(30deg,rgba(255,190,82,.25)_12%,transparent_12.5%,transparent_87%,rgba(255,190,82,.25)_87.5%,rgba(255,190,82,.25)),linear-gradient(150deg,rgba(255,190,82,.25)_12%,transparent_12.5%,transparent_87%,rgba(255,190,82,.25)_87.5%,rgba(255,190,82,.25)),linear-gradient(30deg,rgba(255,190,82,.25)_12%,transparent_12.5%,transparent_87%,rgba(255,190,82,.25)_87.5%,rgba(255,190,82,.25)),linear-gradient(150deg,rgba(255,190,82,.25)_12%,transparent_12.5%,transparent_87%,rgba(255,190,82,.25)_87.5%,rgba(255,190,82,.25))] [background-position:0_0,0_0,18px_31px,18px_31px] [background-size:36px_62px]" />
      <div className="absolute inset-0 bg-[linear-gradient(rgba(255,255,255,.035)_1px,transparent_1px),linear-gradient(90deg,rgba(255,255,255,.035)_1px,transparent_1px)] bg-[size:40px_40px]" />
    </div>
  )
}

function BrandBlock() {
  return (
    <div className="flex items-center gap-4">
      <img className="brand-mark-image" src="/assets/eduhive-logo-mark.png" alt="智学蜂巢 EduHive 标志" />
      <div>
        <h1 className="text-xl font-black leading-tight text-amber-50">智学蜂巢</h1>
        <p className="font-mono text-lg font-bold tracking-[0.12em] text-white">EduHive</p>
      </div>
    </div>
  )
}

const KnowledgePanel = memo(function KnowledgePanel({
  nodes,
  edges,
  plannedPath,
  selectedNodeId,
  selectedConcept,
  graphConcepts,
  averageMastery,
  resourceStatus,
  conceptDetail,
  showDetail,
  focusNonce,
  onNodeSelect,
  onCanvasBlankClick,
  onPlanPath,
  onGenerateResource,
}: {
  nodes: PathNode[]
  edges: KnowledgeEdge[]
  plannedPath: string[]
  selectedNodeId: string
  selectedConcept: string
  graphConcepts: Set<string>
  averageMastery: number
  resourceStatus: string
  conceptDetail: any | null
  showDetail: boolean
  focusNonce: number
  onNodeSelect: (node: PathNode) => void
  onCanvasBlankClick: () => void
  onPlanPath: () => void
  onGenerateResource: (concept: string) => void
}) {
  const selectedNode = nodes.find((node) => node.id === selectedNodeId) ?? nodes[nodes.length - 1]
  const selectedIncomingEdge = edges.find((edge) => edge.target === selectedNode?.title) as (KnowledgeEdge & Record<string, any>) | undefined
  const canvasRef = useRef<HTMLDivElement | null>(null)
  const mapX = useMotionValue(0)
  const [canvasSize, setCanvasSize] = useState({ width: 920, height: 355 })
  const plannedNodeSet = useMemo(() => new Set(plannedPath), [plannedPath])
  const plannedEdgeSet = useMemo(() => {
    const edgeSet = new Set<string>()
    plannedPath.forEach((name, index) => {
      const next = plannedPath[index + 1]
      if (next) edgeSet.add(buildPathEdgeKey(name, next))
    })
    return edgeSet
  }, [plannedPath])
  const nodeByTitle = useMemo(() => new Map(nodes.map((node) => [node.title, node])), [nodes])
  const renderedEdges = useMemo(() => edges
    .map((edge) => {
      const source = nodeByTitle.get(edge.source)
      const target = nodeByTitle.get(edge.target)
      if (!source || !target) return null
      return {
        edge,
        source,
        target,
        d: edgePath(source, target),
        active: plannedEdgeSet.has(buildPathEdgeKey(edge.source, edge.target)),
      }
    })
    .filter((edge): edge is NonNullable<typeof edge> => Boolean(edge)), [edges, nodeByTitle, plannedEdgeSet])
  const activeEdges = useMemo(() => renderedEdges.filter((item) => item.active), [renderedEdges])
  const mapPixelWidth = Math.max(1200, nodes.length * 180)
  const dragLeft = -Math.max(820, mapPixelWidth - 920)
  const nodeX = selectedNode ? (selectedNode.x / 100) * mapPixelWidth : 0
  const nodeY = selectedNode ? (selectedNode.y / 100) * canvasSize.height : 0
  const detailLeft = selectedNode
    ? Math.min(mapPixelWidth - 270, Math.max(12, nodeX + 82))
    : 12
  const detailTop = selectedNode
    ? Math.min(Math.max(12, canvasSize.height - 220), Math.max(12, nodeY - 96))
    : 12

  useEffect(() => {
    const updateCanvasSize = () => {
      const rect = canvasRef.current?.getBoundingClientRect()
      if (!rect) return
      setCanvasSize({ width: rect.width, height: rect.height })
    }
    updateCanvasSize()
    window.addEventListener('resize', updateCanvasSize)
    return () => window.removeEventListener('resize', updateCanvasSize)
  }, [])

  useEffect(() => {
    if (!selectedNode) return
    const centeredOffset = canvasSize.width / 2 - nodeX
    mapX.set(Math.min(0, Math.max(dragLeft, centeredOffset)))
  }, [canvasSize.width, dragLeft, focusNonce, mapX])

  return (
    <Panel className="graph-panel relative min-h-[420px] overflow-hidden">
      <PanelHeader
        title="知识图谱 / 学习路径"
        icon={Network}
        meta={
          <div className="flex flex-wrap gap-4 text-xs">
            <LegendDot color="mint" label="已掌握" />
            <LegendDot color="amber" label="学习中" />
            <LegendDot color="gray" label="待学习" />
            <span className="text-slate-500">--- 前置依赖</span>
          </div>
        }
      />

      <div
        ref={canvasRef}
        className="knowledge-canvas relative h-[calc(100%-54px)] min-h-[355px] overflow-hidden rounded-md border border-white/6 bg-black/12"
        onClick={(event) => {
          if (event.target === event.currentTarget) onCanvasBlankClick()
        }}
      >
        <motion.div
          className="dungeon-map absolute inset-y-0 left-0"
          style={{ width: mapPixelWidth, x: mapX }}
          drag="x"
          dragConstraints={{ left: dragLeft, right: 0 }}
          dragElastic={0.08}
          onClick={(event) => {
            if (event.target === event.currentTarget) onCanvasBlankClick()
          }}
        >
          <svg
            className="absolute inset-0 h-full w-full"
            viewBox="0 0 100 100"
            preserveAspectRatio="none"
            onClick={onCanvasBlankClick}
          >
            {renderedEdges.map(({ edge, d }) => (
              <path key={`${edge.source}-${edge.target}-dependency`} d={d} className="dependency-path" />
            ))}
            {activeEdges.map(({ edge, d }) => (
              <path key={`${edge.source}-${edge.target}-halo`} d={d} className="route-path route-path-halo" />
            ))}
            {activeEdges.map(({ edge, d }) => (
              <path key={`${edge.source}-${edge.target}-glow`} d={d} className="route-path route-path-glow" />
            ))}
          </svg>

          {nodes.map((node, index) => (
            <GraphNode
              key={node.id}
              node={node}
              index={index}
              selected={node.id === selectedNodeId || node.title === selectedConcept}
              detailOpen={showDetail && (node.id === selectedNodeId || node.title === selectedConcept)}
              onPlannedPath={plannedNodeSet.has(node.title)}
              known={graphConcepts.size === 0 || graphConcepts.has(node.title)}
              onSelect={() => onNodeSelect(node)}
            />
          ))}

          {showDetail && selectedNode && (
            <motion.div
              key={selectedNodeId}
              className="target-card"
              style={{ left: detailLeft, top: detailTop }}
              initial={{ opacity: 0, y: 12, scale: 0.96 }}
              animate={{ opacity: 1, y: 0, scale: 1 }}
              transition={{ type: 'spring', stiffness: 260, damping: 22 }}
              onClick={(event) => event.stopPropagation()}
            >
              <p className="font-bold text-amber-300">当前目标：{selectedConcept}</p>
              <p className="mt-2 text-slate-400">
                前置依赖：
                {(() => {
                  const prerequisites = conceptDetail?.prerequisites?.length
                    ? conceptDetail.prerequisites
                    : selectedIncomingEdge?.prerequisites?.length
                      ? selectedIncomingEdge.prerequisites
                    : edges.filter((e) => e.target === selectedNode.title).map((e) => e.source)
                  return prerequisites.length > 0
                    ? prerequisites.join('、')
                    : (plannedPath.slice(0, -1).join('、') || '无前置依赖')
                })()}
              </p>
              {selectedIncomingEdge?.reason && (
                <p className="mt-2 leading-relaxed text-amber-100/80">推荐理由：{selectedIncomingEdge.reason}</p>
              )}
              <div className="mt-2 flex items-center gap-2">
                <span className="text-slate-400">掌握度：</span>
                <strong className="text-amber-200">{averageMastery}%</strong>
                <span className="h-1.5 flex-1 overflow-hidden rounded-full bg-white/10">
                  <span className="block h-full rounded-full bg-gradient-to-r from-amber-500 to-emerald-300" style={{ width: `${averageMastery}%` }} />
                </span>
              </div>
              <p className="mt-2 leading-relaxed text-slate-300">
                易错点：{conceptDetail?.common_errors?.join('、') || selectedIncomingEdge?.pitfalls?.filter(Boolean).join('、') || '后端暂未返回该节点易错点'}
              </p>
              <p className="mt-2 font-mono text-[11px] text-emerald-300">{resourceStatus}</p>
              <div className="mt-3 flex gap-2">
                <button onClick={onPlanPath} className="mini-action">规划路径</button>
                <button onClick={() => onGenerateResource(selectedNode.title)} className="mini-action amber">生成该节点资源</button>
              </div>
            </motion.div>
          )}
        </motion.div>

        <div className="map-hint">拖动地图探索后续副本</div>
      </div>

      <div className="pointer-events-none absolute inset-0 bg-[radial-gradient(circle_at_83%_74%,rgba(245,176,65,.16),transparent_18%)]" />
    </Panel>
  )
})

const GraphNode = memo(function GraphNode({
  node,
  index,
  known,
  selected,
  detailOpen,
  onPlannedPath,
  onSelect,
}: {
  node: PathNode
  index: number
  known: boolean
  selected: boolean
  detailOpen: boolean
  onPlannedPath: boolean
  onSelect: () => void
}) {
  const waveCount = selected ? 2 : onPlannedPath ? 1 : 0

  return (
    <motion.button
      type="button"
      onClick={onSelect}
      className={cn('graph-node text-left', node.state, selected && 'selected', detailOpen && 'detail-open', onPlannedPath && 'on-path', !known && 'opacity-70')}
      style={{ left: `${node.x}%`, top: `${node.y}%` }}
      initial={{ opacity: 0, scale: 0.85 }}
      animate={{ opacity: 1, scale: 1 }}
      transition={{ delay: index * 0.05, duration: 0.35 }}
    >
      {waveCount > 0 && (
        <div className="node-wave-field" aria-hidden="true">
          {Array.from({ length: waveCount }).map((_, index) => <span key={index} />)}
        </div>
      )}
      <div className="graph-node-icon">
        <node.icon className="h-5 w-5" />
      </div>
      <div className="graph-node-label">
        <strong>{node.title}</strong>
        <span>掌握度 {node.mastery}%</span>
      </div>
    </motion.button>
  )
})

function ChatCommand({
  input,
  setInput,
  messages,
  loading,
  targetConcept,
  onSend,
  onContinueTutor,
}: {
  input: string
  setInput: (value: string) => void
  messages: ChatMessage[]
  loading: boolean
  targetConcept: string
  onSend: (messageOverride?: string) => void
  onContinueTutor: () => void
}) {
  const messagesRef = useRef<HTMLDivElement | null>(null)
  const voiceRecognitionRef = useRef<any | null>(null)
  const [voiceStatus, setVoiceStatus] = useState<'idle' | 'listening' | 'unsupported'>('idle')
  const [defaultPromptCleared, setDefaultPromptCleared] = useState(false)
  const defaultPrompt = `我想学习 ${targetConcept}`
  const isDefaultPromptText = (value: string) => /^我想学习\s+/.test(value.trim())
  const inputText = input.trim()
  const sendDisabled = loading || !inputText

  useEffect(() => {
    messagesRef.current?.scrollTo({ top: messagesRef.current.scrollHeight, behavior: 'smooth' })
  }, [messages])

  useEffect(() => {
    return () => {
      voiceRecognitionRef.current?.stop?.()
      voiceRecognitionRef.current = null
    }
  }, [])

  useEffect(() => {
    if (!defaultPromptCleared && isDefaultPromptText(input)) {
      setInput(defaultPrompt)
    }
  }, [defaultPrompt, defaultPromptCleared])

  const handleInputFocus = () => {
    if (isDefaultPromptText(input)) {
      setDefaultPromptCleared(true)
      setInput('')
    }
  }

  const handleInputBlur = () => {
    if (!input.trim()) {
      setInput(defaultPrompt)
      setDefaultPromptCleared(false)
    }
  }

  const handleSend = () => {
    if (sendDisabled) return
    onSend(inputText)
  }

  const toggleVoiceInput = () => {
    if (voiceStatus === 'listening' && voiceRecognitionRef.current) {
      voiceRecognitionRef.current.stop()
      voiceRecognitionRef.current = null
      setVoiceStatus('idle')
      return
    }

    const SpeechRecognition = (window as any).SpeechRecognition || (window as any).webkitSpeechRecognition
    if (!SpeechRecognition) {
      setVoiceStatus('unsupported')
      return
    }

    const recognition = new SpeechRecognition()
    recognition.lang = 'zh-CN'
    recognition.interimResults = false
    recognition.maxAlternatives = 1
    recognition.onstart = () => setVoiceStatus('listening')
    recognition.onend = () => {
      voiceRecognitionRef.current = null
      setVoiceStatus('idle')
    }
    recognition.onerror = () => {
      voiceRecognitionRef.current = null
      setVoiceStatus('idle')
    }
    recognition.onresult = (event: any) => {
      const transcript = String(event.results?.[0]?.[0]?.transcript || '').trim()
      if (transcript) {
        const current = isDefaultPromptText(input) ? '' : input.trim()
        setDefaultPromptCleared(false)
        setInput(current ? `${current} ${transcript}` : transcript)
      }
    }
    voiceRecognitionRef.current = recognition
    recognition.start()
  }

  return (
    <Panel className="chat-command-panel">
      <PanelHeader
        title="AI 学习对话"
        subtitle="Socrates / Navigator / Profiler"
        icon={MessageSquare}
        meta={<span className="flex items-center gap-2 text-xs text-emerald-300"><span className="h-2 w-2 rounded-full bg-emerald-400" />后端对话接口</span>}
      />
      <div className="chat-shell">
        <div className="chat-context-strip">
          <span>当前学习目标</span>
          <strong>{targetConcept}</strong>
          <em>提问后会调用后端 Agent 编排链路，并记录到学习画像。</em>
        </div>

        <div ref={messagesRef} className="chat-message-list">
          {messages.map((message) => (
            <motion.div
              key={message.id}
              className={cn('chat-message-row', message.role === 'user' && 'user', message.role === 'system' && 'system')}
              initial={{ opacity: 0, y: 12 }}
              animate={{ opacity: 1, y: 0 }}
            >
              {message.role !== 'user' && <HexAvatar icon={message.role === 'system' ? Server : Brain} tone={message.role === 'system' ? 'amber' : 'mint'} />}
              <div className="dialogue-bubble">
                <div className="chat-message-meta">
                  <strong>{message.role === 'user' ? '你' : message.agentName || 'AI 助教'}</strong>
                  <span>{message.timestamp}</span>
                </div>
                {message.tutorPayload ? (
                  <SocraticPanel
                    question={message.tutorPayload.question}
                    hint={message.tutorPayload.hint}
                    answer={message.tutorPayload.answer}
                    canProvideAnswer={message.tutorPayload.canProvideAnswer}
                    stage={message.tutorPayload.stage}
                    onNext={onContinueTutor}
                  />
                ) : (
                  <p>{message.content}</p>
                )}
                {message.isStreaming && (
                  <span className="chat-streaming">
                    <i className="typing-dot" />
                    <i className="typing-dot" />
                    <i className="typing-dot" />
                    正在思考
                  </span>
                )}
              </div>
              {message.role === 'user' && <HexAvatar icon={UserRound} tone="amber" />}
            </motion.div>
          ))}
        </div>

        <div className="chat-composer">
          <div className="chat-suggestions">
            {['解释当前知识点', '给我一道练习', '我哪里没掌握'].map((text) => (
              <button
                type="button"
                key={text}
                onClick={() => {
                  setDefaultPromptCleared(false)
                  setInput(text)
                }}
              >
                {text}
              </button>
            ))}
          </div>
          <div className="chat-input-frame">
            <input
              value={input}
              onFocus={handleInputFocus}
              onBlur={handleInputBlur}
              onChange={(event) => {
                const value = event.target.value
                setInput(value)
                setDefaultPromptCleared(!value.trim())
              }}
              onKeyDown={(event) => {
                if (event.key === 'Enter' && !event.nativeEvent.isComposing && !sendDisabled) handleSend()
              }}
              className="min-w-0 flex-1 bg-transparent px-3 text-sm text-slate-900 outline-none placeholder:text-slate-400"
              placeholder="输入你的问题，例如：为什么 open 要写 encoding？"
            />
            <button
              type="button"
              onClick={toggleVoiceInput}
              className={cn('voice-button', voiceStatus === 'listening' && 'listening', voiceStatus === 'unsupported' && 'unsupported')}
              title={voiceStatus === 'unsupported' ? '当前浏览器不支持语音输入' : voiceStatus === 'listening' ? '正在听，点击停止' : '语音输入'}
              aria-label={voiceStatus === 'listening' ? '停止语音输入' : '语音输入'}
            >
              <Mic className="h-4 w-4" />
            </button>
            <button type="button" onMouseDown={(event) => event.preventDefault()} onClick={handleSend} disabled={sendDisabled} className="send-button">
              {loading ? <Loader2 className="h-4 w-4 animate-spin" /> : <Send className="h-4 w-4 fill-current" />}
            </button>
          </div>
        </div>
      </div>
    </Panel>
  )
}

function CodeCommand({
  code,
  setCode,
  output,
  variables,
  loading,
  onRun,
  onReset,
}: {
  code: string
  setCode: (value: string) => void
  output: string
  variables: CodeVariable[]
  loading: boolean
  onRun: () => void
  onReset: () => void
}) {
  const hasRunOutput = output.trim().length > 0 && output !== SAMPLE_OUTPUT
  const displayVariables = useMemo(() => {
    const normalized = normalizeCodeVariables(variables)
    return normalized.length ? normalized : inferCodeVariables(code, output)
  }, [code, output, variables])

  return (
    <Panel className="min-h-[300px]">
      <PanelHeader
        title="代码沙箱"
        subtitle="后端受控执行 / 变量快照"
        icon={Code2}
        meta={
          <div className="flex gap-2">
            <button onClick={onRun} disabled={loading} className="run-button">
              {loading ? <Loader2 className="h-3.5 w-3.5 animate-spin" /> : <Play className="h-3.5 w-3.5 fill-current" />}
              运行
            </button>
            <button onClick={onReset} className="tool-button"><RefreshCw className="h-3.5 w-3.5" />重置</button>
          </div>
        }
      />
      <div className="grid h-[calc(100%-54px)] min-h-[230px] gap-3 lg:grid-cols-[1fr_0.82fr]">
        <div className="code-editor">
          <div className="code-lines">
            {code.split('\n').map((line, index) => (
              <div key={`${line}-${index}`}>
                <span>{index + 1}</span>
                <code>{line}</code>
              </div>
            ))}
          </div>
          <textarea value={code} onChange={(event) => setCode(event.target.value)} aria-label="Python code editor" />
        </div>
        <div className="grid gap-3 md:grid-cols-2 lg:grid-cols-1 xl:grid-cols-2">
          <div className="console-box">
            <p className="console-title">输出</p>
            <pre>{output}</pre>
          </div>
          <div className="console-box">
            <p className="console-title">
              变量快照
              <span>{displayVariables.length ? `${displayVariables.length} 个` : '等待运行'}</span>
            </p>
            {displayVariables.length ? (
              <div className="variable-stack">
                {displayVariables.map((item) => (
                  <div className="variable-row" key={`${item.name}-${item.type}`}>
                    <div className="variable-head">
                      <code>{item.name}</code>
                      <span>{item.type}</span>
                    </div>
                    <pre>{item.value}</pre>
                    {typeof item.size === 'number' && <small>len = {item.size}</small>}
                  </div>
                ))}
              </div>
            ) : (
              <div className="variable-empty">
                <Braces className="h-4 w-4" />
                <span>{hasRunOutput ? '本次运行没有检测到可展示的顶层变量。请确认代码中存在变量赋值。' : '运行代码后，这里会显示后端返回的变量名、类型和值。'}</span>
              </div>
            )}
          </div>
        </div>
      </div>
    </Panel>
  )
}

function LegendDot({ color, label }: { color: 'mint' | 'amber' | 'gray'; label: string }) {
  return (
    <span className="flex items-center gap-2">
      <i className={cn('h-2.5 w-2.5 rounded-full', color === 'mint' && 'bg-emerald-300', color === 'amber' && 'bg-amber-300', color === 'gray' && 'bg-slate-500')} />
      {label}
    </span>
  )
}

function TeacherWorkspace({ onBack, onLogout }: { onBack: () => void; onLogout: () => void }) {
  const [courses, setCourses] = useState<CourseRecord[]>([])
  const [materialsByCourse, setMaterialsByCourse] = useState<Record<string, CourseMaterial[]>>({})
  const [loading, setLoading] = useState(false)
  const [uploadingCourseId, setUploadingCourseId] = useState('')
  const [status, setStatus] = useState('这里会显示你当前账号下已保存的课程。')
  const [form, setForm] = useState({ title: '', category: '程序设计', summary: '' })
  const coursesRef = useRef<CourseRecord[]>([])
  const courseCount = courses.length
  const publishedCount = courses.filter((course) => course.status === 'published').length
  const pendingReviewCount = courses.filter((course) => course.status === 'pending_review').length
  const draftCount = courses.filter((course) => course.status === 'draft').length

  const loadMaterialsForCourses = useCallback(async (courseList: CourseRecord[]) => {
    const entries = await Promise.all(courseList.map(async (course) => {
      try {
        const res = await teacherApi.getCourseMaterials(course.course_id)
        return [course.course_id, res.data.materials] as const
      } catch {
        return [course.course_id, []] as const
      }
    }))
    setMaterialsByCourse(Object.fromEntries(entries))
  }, [])

  const refreshCourseMaterials = useCallback(async (courseId: string) => {
    try {
      const res = await teacherApi.getCourseMaterials(courseId)
      setMaterialsByCourse((current) => ({ ...current, [courseId]: res.data.materials }))
      return res.data.materials
    } catch {
      setStatus('课程资料暂时无法刷新，请稍后重试。')
      return []
    }
  }, [])

  const loadCourses = useCallback(async () => {
    setLoading(true)
    try {
      const res = await teacherApi.getCourses()
      setCourses(res.data.courses)
      await loadMaterialsForCourses(res.data.courses)
      setStatus(res.data.courses.length ? '已载入你的课程。' : '当前账号还没有课程，先添加一门吧。')
    } catch (error: any) {
      setStatus(error?.response?.data?.detail || '课程暂时加载失败，请稍后重试。')
    } finally {
      setLoading(false)
    }
  }, [loadMaterialsForCourses])

  useEffect(() => {
    loadCourses()
  }, [loadCourses])

  useEffect(() => {
    coursesRef.current = courses
  }, [courses])

  const syncCourseStatuses = useCallback(async () => {
    try {
      const res = await teacherApi.getCourses()
      const currentStatusById = new Map(coursesRef.current.map((course) => [course.course_id, course.status]))
      const hasStatusChange = res.data.courses.some((course) => {
        const previousStatus = currentStatusById.get(course.course_id)
        return previousStatus && previousStatus !== course.status
      })
      setCourses(res.data.courses)
      if (hasStatusChange) setStatus('课程审核状态已同步。')
    } catch {
      // 后台轻量同步失败时不打断教师正在进行的操作。
    }
  }, [])

  useEffect(() => {
    const handleVisibleSync = () => {
      if (document.visibilityState === 'visible') void syncCourseStatuses()
    }
    const timer = window.setInterval(() => {
      if (document.visibilityState === 'visible') void syncCourseStatuses()
    }, 12000)

    window.addEventListener('focus', handleVisibleSync)
    document.addEventListener('visibilitychange', handleVisibleSync)
    return () => {
      window.clearInterval(timer)
      window.removeEventListener('focus', handleVisibleSync)
      document.removeEventListener('visibilitychange', handleVisibleSync)
    }
  }, [syncCourseStatuses])

  const submitCourse = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault()
    if (!form.title.trim() || !form.summary.trim()) {
      setStatus('请填写课程名称和课程简介。')
      return
    }
    setLoading(true)
    try {
      const res = await teacherApi.createCourse({
        title: form.title.trim(),
        category: form.category.trim() || '未分类',
        summary: form.summary.trim(),
        status: 'draft',
      })
      setCourses((current) => [res.data.course, ...current])
      setMaterialsByCourse((current) => ({ ...current, [res.data.course.course_id]: [] }))
      setForm({ title: '', category: '程序设计', summary: '' })
      setStatus(`课程「${res.data.course.title}」已保存。`)
    } catch (error: any) {
      setStatus(error?.response?.data?.detail || '新增课程失败。')
    } finally {
      setLoading(false)
    }
  }

  const updateStatus = async (course: CourseRecord, nextStatus: string) => {
    setLoading(true)
    try {
      const res = await teacherApi.updateCourse(course.course_id, { status: nextStatus })
      setCourses((current) => current.map((item) => item.course_id === course.course_id ? res.data.course : item))
      setStatus(`课程「${course.title}」已${nextStatus === 'pending_review' ? '提交审核' : nextStatus === 'draft' ? '设为草稿' : getCourseStatusLabel(nextStatus)}。`)
    } catch (error: any) {
      setStatus(error?.response?.data?.detail || '课程状态更新失败。')
    } finally {
      setLoading(false)
    }
  }

  const removeCourse = async (course: CourseRecord) => {
    const materialCount = (materialsByCourse[course.course_id] || []).length
    const confirmed = window.confirm(
      materialCount
        ? `确定删除课程「${course.title}」吗？该课程下的 ${materialCount} 个资料也会一起删除。`
        : `确定删除课程「${course.title}」吗？`,
    )
    if (!confirmed) return
    setLoading(true)
    try {
      const res = await teacherApi.deleteCourse(course.course_id)
      setCourses(res.data.courses)
      setMaterialsByCourse((current) => {
        const next = { ...current }
        delete next[course.course_id]
        return next
      })
      setStatus(`课程「${course.title}」已删除。`)
    } catch (error: any) {
      setStatus(error?.response?.data?.detail || '课程删除失败。')
    } finally {
      setLoading(false)
    }
  }

  const uploadMaterial = async (course: CourseRecord, file?: File) => {
    if (!file) return
    setUploadingCourseId(course.course_id)
    try {
      const formData = new FormData()
      formData.append('file', file)
      const res = await teacherApi.uploadCourseMaterial(course.course_id, formData)
      setMaterialsByCourse((current) => ({ ...current, [course.course_id]: res.data.materials }))
      if (res.data.course) {
        setCourses((current) => current.map((item) => item.course_id === course.course_id ? res.data.course! : item))
      }
      setStatus(`资料「${file.name}」已添加到「${course.title}」。`)
    } catch (error: any) {
      setStatus(error?.response?.data?.detail || '资料上传失败，请检查文件后重试。')
    } finally {
      setUploadingCourseId('')
    }
  }

  const removeMaterial = async (course: CourseRecord, material: CourseMaterial) => {
    setUploadingCourseId(course.course_id)
    try {
      const res = await teacherApi.deleteCourseMaterial(material.material_id)
      setMaterialsByCourse((current) => ({ ...current, [course.course_id]: res.data.materials }))
      if (res.data.course) {
        setCourses((current) => current.map((item) => item.course_id === course.course_id ? res.data.course! : item))
      }
      setStatus(`资料「${material.original_filename}」已移除。`)
    } catch (error: any) {
      setStatus(error?.response?.data?.detail || '资料删除失败。')
    } finally {
      setUploadingCourseId('')
    }
  }

  const downloadMaterial = async (material: CourseMaterial) => {
    try {
      const res = await teacherApi.downloadCourseMaterial(material.material_id)
      const blob = new Blob([res.data], { type: material.mime_type || 'application/octet-stream' })
      const url = URL.createObjectURL(blob)
      const link = document.createElement('a')
      link.href = url
      link.download = material.original_filename
      document.body.appendChild(link)
      link.click()
      link.remove()
      URL.revokeObjectURL(url)
    } catch {
      setStatus('资料下载失败，请稍后重试。')
    }
  }

  return (
    <div className="teacher-page">
      <header className="portal-nav teacher-nav">
        <BrandBlock />
        <nav aria-label="教师端导航">
          <button type="button" onClick={onBack}><Home className="h-4 w-4" />课程广场</button>
          <button type="button" onClick={onLogout}><LockKeyhole className="h-4 w-4" />退出登录</button>
        </nav>
      </header>
      <main className="portal-main teacher-main">
        <section className="portal-hero teacher-hero">
          <div className="portal-hero-copy">
            <p className="portal-kicker">教师课程工作台</p>
            <h1><span>创建课程并管理课堂内容</span></h1>
            <span>在这里你可以新建课程、上传资料并提交审核，课程会在管理端通过后再对学生开放。</span>
            <div className="portal-hero-chips" aria-label="教师端能力">
              <span><BookOpen className="h-3.5 w-3.5" />课程创建</span>
              <span><Layers3 className="h-3.5 w-3.5" />课程管理</span>
              <span><FileUp className="h-3.5 w-3.5" />资料上传</span>
            </div>
          </div>
          <div className="portal-hero-side">
            <form className="portal-login-card teacher-form-card" onSubmit={submitCourse}>
              <strong>添加课程</strong>
              <span className="teacher-form-note">填写完成后点保存，课程会出现在下方列表里。</span>
              <label>
                <span>课程名称</span>
                <input value={form.title} onChange={(event) => setForm({ ...form, title: event.target.value })} placeholder="例如：Python 程序设计基础" />
              </label>
              <label>
                <span>课程分类</span>
                <input value={form.category} onChange={(event) => setForm({ ...form, category: event.target.value })} placeholder="例如：程序设计" />
              </label>
              <label>
                <span>课程简介</span>
                <textarea value={form.summary} onChange={(event) => setForm({ ...form, summary: event.target.value })} placeholder="说明课程面向对象和学习目标" />
              </label>
              <button type="submit" disabled={loading}>{loading ? '提交中...' : '保存课程'}</button>
            </form>

            <section className="portal-login-card teacher-summary-card">
              <strong>课程概览</strong>
              <div className="teacher-summary-grid">
                <div>
                  <span>总课程数</span>
                  <b>{courseCount}</b>
                </div>
                <div>
                  <span>草稿</span>
                  <b>{draftCount}</b>
                </div>
                <div>
                  <span>待审核</span>
                  <b>{pendingReviewCount}</b>
                </div>
                <div>
                  <span>已发布</span>
                  <b>{publishedCount}</b>
                </div>
              </div>
              <p>{loading ? '正在刷新课程...' : status}</p>
            </section>
          </div>
        </section>

        <section className="portal-section teacher-courses-section">
          <div className="portal-section-title">
            <div>
              <p>我的课程</p>
              <h2>{courseCount ? `共 ${courseCount} 门课程` : '暂无课程'}</h2>
            </div>
            <span>下方展示的是你当前账号下的课程，修改后会同步到课程列表。</span>
          </div>
          {courses.length ? (
            <div className="course-card-grid teacher-course-grid">
              {courses.map((course) => (
                <article key={course.course_id} className="course-card course-card-teal teacher-course-card">
                  <div className="course-card-cover">
                    <BookOpen className="h-7 w-7" />
                    <span>{getCourseStatusLabel(course.status)}</span>
                  </div>
                  <div className="course-card-body">
                    <p>{course.category} · {course.teacher_username}</p>
                    <h3>{course.title}</h3>
                    <span>{course.summary}</span>
                    <div className="course-card-meta">
                      <em><Clock3 className="h-3.5 w-3.5" />更新 {course.updated_at.slice(0, 10)}</em>
                      <em><UserRound className="h-3.5 w-3.5" />创建者 {course.teacher_username}</em>
                    </div>
                    <div className="course-card-tags">
                      <i>{course.course_id.slice(0, 8)}</i>
                      <i>{getCourseStatusLabel(course.status)}</i>
                    </div>
                    <div className="teacher-material-panel">
                      <div className="teacher-material-head">
                        <span>课程资料</span>
                        <label className={cn('teacher-upload-chip', uploadingCourseId === course.course_id && 'is-busy')}>
                          <FileUp className="h-3.5 w-3.5" />
                          {uploadingCourseId === course.course_id ? '处理中...' : '上传资料'}
                          <input
                            type="file"
                            accept=".pdf,.doc,.docx,.ppt,.pptx,.md,.txt,.py,.zip,.png,.jpg,.jpeg"
                            disabled={uploadingCourseId === course.course_id}
                            onChange={(event) => {
                              const file = event.currentTarget.files?.[0]
                              if (file) void uploadMaterial(course, file)
                              event.currentTarget.value = ''
                            }}
                          />
                        </label>
                      </div>
                      {(materialsByCourse[course.course_id] || []).length ? (
                        <div className="teacher-material-list">
                          {(materialsByCourse[course.course_id] || []).map((material) => (
                            <article key={material.material_id}>
                              <FileUp className="h-3.5 w-3.5" />
                              <div>
                                <strong>{material.original_filename}</strong>
                                <span>{formatFileSize(material.file_size)} · {material.created_at.slice(0, 10)}</span>
                              </div>
                              <button type="button" onClick={() => void downloadMaterial(material)} title="下载资料">
                                <Download className="h-3.5 w-3.5" />
                              </button>
                              <button type="button" onClick={() => void removeMaterial(course, material)} title="删除资料">
                                <Trash2 className="h-3.5 w-3.5" />
                              </button>
                            </article>
                          ))}
                        </div>
                      ) : (
                        <button type="button" className="teacher-material-empty" onClick={() => void refreshCourseMaterials(course.course_id)}>
                          暂无资料，上传课件或讲义后学生可查看
                        </button>
                      )}
                    </div>
                  </div>
                  <strong className="teacher-course-actions">
                    <span className="teacher-status-label">课程状态</span>
                    <span className="teacher-status-toggle" role="group" aria-label="课程状态">
                      <button
                        type="button"
                        className={course.status === 'draft' ? 'active' : ''}
                        aria-pressed={course.status === 'draft'}
                        onClick={() => updateStatus(course, 'draft')}
                      >
                        草稿
                      </button>
                      <button
                        type="button"
                        className={course.status === 'pending_review' ? 'active' : ''}
                        aria-pressed={course.status === 'pending_review'}
                        onClick={() => updateStatus(course, 'pending_review')}
                      >
                        提交审核
                      </button>
                    </span>
                    <button type="button" className="danger" onClick={() => void removeCourse(course)}>删除</button>
                  </strong>
                </article>
              ))}
            </div>
          ) : (
            <div className="course-empty-result teacher-empty-result">
              <Layers3 className="h-6 w-6" />
              <strong>还没有课程</strong>
              <span>先在右侧添加一门课程，保存后就会显示在这里。</span>
            </div>
          )}
        </section>
      </main>
      <FloatingAssistant activeNav="resources" selectedConcept="教师工作台" roleContext="teacher" />
    </div>
  )
}

function AdminWorkspace({ onBack, onLogout }: { onBack: () => void; onLogout: () => void }) {
  const [stats, setStats] = useState<Record<string, number>>({})
  const [users, setUsers] = useState<Array<{ username: string; role: UserRole; created_at: string }>>([])
  const [courses, setCourses] = useState<AdminCourseRecord[]>([])
  const [loading, setLoading] = useState(false)
  const [status, setStatus] = useState('正在加载管理概览。')

  const loadAdminData = useCallback(async () => {
    setLoading(true)
    try {
      const [statsRes, usersRes, coursesRes] = await Promise.all([
        adminApi.getStats(),
        adminApi.getUsers(),
        adminApi.getCourses(),
      ])
      setStats(statsRes.data.stats)
      setUsers(usersRes.data.users)
      setCourses(coursesRes.data.courses)
      setStatus('管理概览已更新。')
    } catch (error: any) {
      setStatus(error?.response?.data?.detail || '管理概览暂时不可用，请确认当前账号是管理员。')
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    loadAdminData()
  }, [loadAdminData])

  const setCourseStatus = async (course: AdminCourseRecord, nextStatus: string) => {
    setLoading(true)
    try {
      const res = await adminApi.updateCourse(course.course_id, { status: nextStatus })
      setCourses((current) => current.map((item) => item.course_id === course.course_id ? res.data.course : item))
      setStatus(`课程「${course.title}」状态已更新。`)
    } catch (error: any) {
      setStatus(error?.response?.data?.detail || '课程状态更新失败。')
    } finally {
      setLoading(false)
    }
  }

  const downloadAdminMaterial = async (material: CourseMaterial) => {
    try {
      const res = await teacherApi.downloadCourseMaterial(material.material_id)
      const blob = new Blob([res.data], { type: material.mime_type || 'application/octet-stream' })
      const url = URL.createObjectURL(blob)
      const link = document.createElement('a')
      link.href = url
      link.download = material.original_filename
      document.body.appendChild(link)
      link.click()
      link.remove()
      URL.revokeObjectURL(url)
    } catch (error: any) {
      setStatus(error?.response?.data?.detail || '课程资料下载失败。')
    }
  }

  return (
    <div className="course-portal min-h-screen admin-page">
      <header className="portal-nav admin-nav">
        <BrandBlock />
        <nav className="portal-login" aria-label="管理端操作">
          <button type="button" onClick={onBack}><Home className="h-4 w-4" />课程广场</button>
          <button type="button" onClick={onLogout}><LockKeyhole className="h-4 w-4" />退出登录</button>
        </nav>
      </header>
      <main className="portal-main admin-main">
        <section className="portal-hero admin-hero">
          <div className="portal-hero-copy">
            <p className="portal-kicker">平台管理中心</p>
            <h1>
              <span>管理平台与课程</span>
              <span>统一维护用户、课程和运行概览</span>
            </h1>
            <span>在这里可以查看平台概览、审核教师提交的课程，并直接看到课程内容与上传资料。</span>
            <div className="portal-hero-chips" aria-label="管理端能力">
              <span><UserRound className="h-3.5 w-3.5" />用户管理</span>
              <span><ShieldCheck className="h-3.5 w-3.5" />课程审核</span>
              <span><BarChart3 className="h-3.5 w-3.5" />平台概览</span>
              <span><LockKeyhole className="h-3.5 w-3.5" />权限控制</span>
            </div>
          </div>
          <aside className="portal-login-card admin-summary-card">
            <strong>管理概览</strong>
            <div className="admin-summary-grid">
              {[
                ['用户', stats.users],
                ['课程', stats.courses],
                ['会话', stats.sessions],
                ['资源', stats.resources],
              ].map(([label, value]) => (
                <div key={label}>
                  <span>{label}</span>
                  <strong>{typeof value === 'number' ? value : 0}</strong>
                </div>
              ))}
            </div>
            <p className="admin-status">{loading ? '正在更新概览...' : status}</p>
          </aside>
        </section>

        <section className="admin-stat-row">
          {[
            ['用户', stats.users],
            ['课程', stats.courses],
            ['会话', stats.sessions],
            ['资源', stats.resources],
          ].map(([label, value]) => (
            <article key={label}>
              <span>{label}</span>
              <strong>{typeof value === 'number' ? value : 0}</strong>
            </article>
          ))}
        </section>

        <section className="admin-grid">
          <section className="portal-section admin-panel">
            <div className="role-panel-title">
              <UserRound className="h-5 w-5" />
              <div>
                <h2>用户管理</h2>
                <span>{users.length ? `共 ${users.length} 个账号` : '暂无用户'}</span>
              </div>
            </div>
            {users.length ? users.map((user) => (
              <article className="role-user-row" key={user.username}>
                <strong>{user.username}</strong>
                <span>{user.role}</span>
              </article>
            )) : <div className="role-empty-state">当前暂无用户。</div>}
          </section>

          <section className="portal-section admin-panel admin-panel-wide">
            <div className="role-panel-title">
              <ShieldCheck className="h-5 w-5" />
              <div>
                <h2>课程管理</h2>
                <span>{courses.length ? `共 ${courses.length} 门课程` : '暂无课程'}</span>
              </div>
            </div>
            {courses.length ? (
              <div className="role-course-list">
                {courses.map((course) => (
                  <article key={course.course_id}>
                    <div>
                      <strong>{course.title}</strong>
                      <span>{course.category} · {course.teacher_username} · {getCourseStatusLabel(course.status)}</span>
                      <p>{course.summary}</p>
                      <div className="admin-course-materials">
                        <span>课程内容</span>
                        <div className="admin-course-material-list">
                          {(course.materials || []).length ? (
                            course.materials!.map((material) => (
                              <article key={material.material_id}>
                                <div>
                                  <strong>{material.original_filename}</strong>
                                  <span>{formatFileSize(material.file_size)} · {material.note || '无备注'}</span>
                                </div>
                                <button type="button" onClick={() => void downloadAdminMaterial(material)} title="下载资料">
                                  <Download className="h-3.5 w-3.5" />
                                </button>
                              </article>
                            ))
                          ) : (
                            <div className="admin-course-empty-material">暂无课程资料</div>
                          )}
                        </div>
                      </div>
                    </div>
                    <div className="admin-course-actions">
                      {course.status === 'published' ? (
                        <button type="button" disabled>已发布</button>
                      ) : (
                        <button type="button" onClick={() => setCourseStatus(course, 'published')}>发布课程</button>
                      )}
                      <button type="button" onClick={() => setCourseStatus(course, 'draft')}>退回修改</button>
                    </div>
                  </article>
                ))}
              </div>
            ) : (
              <div className="role-empty-state">当前暂无课程。</div>
            )}
            <p className="role-panel-note">{loading ? '正在更新...' : status}</p>
          </section>
        </section>
      </main>
      <FloatingAssistant activeNav="profile" selectedConcept="管理工作台" roleContext="admin" />
    </div>
  )
}

export default App

