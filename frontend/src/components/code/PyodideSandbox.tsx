/**
 * 需求：浏览器端 Python 代码沙箱。
 * 功能：
 *   - 基于 Pyodide 在浏览器中加载 Python 解释器；
 *   - 提供 Monaco 编辑器编辑、运行、重置代码；
 *   - 捕获 stdout/stderr 并在终端输出区展示。
 * 主要 hooks/函数：
 *   - runCode：配置标准输出并异步执行 Python 代码；
 *   - reset：恢复默认示例代码。
 * TODO:
 *  - [已完成] Pyodide 动态加载与运行
 *  - [已完成] Monaco 编辑器集成
 *  - [待完成] 多文件/模块支持与包管理（micropip）
 *  - [待完成] 运行超时与资源限制
 *  - [待完成] 代码执行历史与 Diff 对比
 */
import { useEffect, useState } from 'react'
import Editor from '@monaco-editor/react'
import { Play, RotateCcw, Terminal, Loader2 } from 'lucide-react'

import { Button } from '@/components/ui/button'
import { GlassCard } from '@/components/ui/glass-card'
import { IconBox } from '@/components/ui/icon-box'
import { Badge } from '@/components/ui/badge'
import { useSandboxStore } from '@/stores/sandboxStore'
import { cn } from '@/lib/utils'

// Pyodide 单例，避免重复下载和初始化
let pyodideInstance: any = null

const DEFAULT_CODE = '# 在这里输入 Python 代码\nprint("Hello, Python!")'

export function PyodideSandbox() {
  const storeCode = useSandboxStore((s) => s.code)
  const [code, setCode] = useState(storeCode || DEFAULT_CODE)
  const [output, setOutput] = useState('')
  const [error, setError] = useState(false)
  const [loading, setLoading] = useState(true)
  const [running, setRunning] = useState(false)

  // 当 ChatPanel / ResourceViewer 写入代码时同步到编辑器
  useEffect(() => {
    setCode(storeCode || DEFAULT_CODE)
  }, [storeCode])

  // 动态加载 Pyodide 运行时（首次访问沙箱时触发）
  useEffect(() => {
    const load = async () => {
      if (!pyodideInstance) {
        const { loadPyodide } = await import('pyodide')
        pyodideInstance = await loadPyodide({
          indexURL: 'https://cdn.jsdelivr.net/pyodide/v0.26.1/full/',
        })
      }
      setLoading(false)
    }
    load()
  }, [])

  // 配置 stdout/stderr 捕获，异步执行 Python 代码
  const runCode = async () => {
    if (!pyodideInstance) return
    setRunning(true)
    setOutput('')
    setError(false)

    const stdout: string[] = []
    const stderr: string[] = []

    pyodideInstance.setStdout({ batched: (text: string) => stdout.push(text) })
    pyodideInstance.setStderr({ batched: (text: string) => stderr.push(text) })

    try {
      await pyodideInstance.runPythonAsync(code)
      setOutput(stdout.join('') || '（无输出）')
    } catch (err: any) {
      setError(true)
      setOutput(`错误：${err.message}\n${stderr.join('')}`)
    } finally {
      setRunning(false)
    }
  }

  // 恢复默认示例代码
  const reset = () => setCode(DEFAULT_CODE)

  return (
    <GlassCard className="flex h-[calc(100vh-12rem)] min-h-[520px] flex-col overflow-hidden" hover={false}>
      <div className="flex flex-row items-center justify-between border-b border-slate-100 bg-gradient-to-r from-emerald-50/50 to-teal-50/50 px-5 py-4">
        <div className="flex items-center gap-3">
          <IconBox icon={Terminal} variant="emerald" size="sm" />
          <div>
            <h3 className="text-base font-bold text-slate-900">Python 代码沙箱</h3>
            <p className="text-xs text-slate-500">浏览器内 Pyodide 运行环境</p>
          </div>
        </div>
        <div className="flex items-center gap-2">
          <Badge
            variant="secondary"
            className={cn(
              'rounded-lg text-xs font-semibold',
              loading ? 'bg-amber-100 text-amber-700' : 'bg-emerald-100 text-emerald-700'
            )}
          >
            {loading ? 'Pyodide 加载中' : 'Pyodide 就绪'}
          </Badge>
          <Button variant="outline" size="sm" className="rounded-lg" onClick={reset} disabled={loading || running}>
            <RotateCcw className="mr-1.5 h-3.5 w-3.5" /> 清空
          </Button>
          <Button
            size="sm"
            className="rounded-lg bg-gradient-to-r from-emerald-600 to-teal-600 shadow-lg shadow-emerald-500/25 transition-transform active:scale-95"
            onClick={runCode}
            disabled={loading || running}
          >
            {running ? (
              <Loader2 className="mr-1.5 h-3.5 w-3.5 animate-spin" />
            ) : (
              <Play className="mr-1.5 h-3.5 w-3.5" />
            )}
            {running ? '运行中' : '运行'}
          </Button>
        </div>
      </div>

      <div className="flex flex-1 flex-col gap-4 overflow-hidden p-5">
        {loading ? (
          <div className="flex flex-1 flex-col items-center justify-center gap-3 text-slate-500">
            <Loader2 className="h-8 w-8 animate-spin text-emerald-500" />
            <span className="text-sm">正在加载 Pyodide 运行环境...</span>
          </div>
        ) : (
          <>
            <div className="relative flex-1 overflow-hidden rounded-2xl border border-slate-200 shadow-inner">
              <Editor
                height="100%"
                defaultLanguage="python"
                value={code}
                onChange={(value) => setCode(value || '')}
                theme="vs-dark"
                options={{
                  minimap: { enabled: false },
                  fontSize: 14,
                  fontFamily: 'JetBrains Mono, monospace',
                  lineNumbers: 'on',
                  roundedSelection: false,
                  scrollBeyondLastLine: false,
                  automaticLayout: true,
                  padding: { top: 16 },
                  wordWrap: 'on',
                }}
              />
            </div>

            <div className="flex h-48 flex-col overflow-hidden rounded-2xl border border-slate-200 bg-slate-950 shadow-inner">
              <div className="flex items-center justify-between border-b border-slate-800 px-4 py-2.5">
                <div className="flex items-center gap-2 text-xs font-bold text-slate-400">
                  <Terminal className="h-3.5 w-3.5" />
                  终端输出
                </div>
                {output && (
                  <Badge
                    variant="outline"
                    className={cn(
                      'h-5 rounded border-0 px-2 text-[10px] font-bold',
                      error ? 'bg-red-500/10 text-red-400' : 'bg-emerald-500/10 text-emerald-400'
                    )}
                  >
                    {error ? 'Error' : 'Done'}
                  </Badge>
                )}
              </div>
              <div className="flex-1 overflow-auto p-4">
                <pre
                  className={cn(
                    'whitespace-pre-wrap font-mono text-xs leading-relaxed',
                    error ? 'text-red-300' : 'text-slate-200'
                  )}
                >
                  {output || (
                    <span className="text-slate-600">运行代码后，输出将显示在这里...</span>
                  )}
                </pre>
              </div>
            </div>
          </>
        )}
      </div>
    </GlassCard>
  )
}
