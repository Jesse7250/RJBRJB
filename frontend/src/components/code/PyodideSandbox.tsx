import { Play, RotateCcw } from 'lucide-react'
import { useEffect, useState } from 'react'

import { Button } from '@/components/ui/button'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { useSandboxStore } from '@/stores/sandboxStore'

/**
 * TODO:
 * - [已完成] 与练习题联动，支持一键载入题目代码（通过 sandboxStore）
 * - [待完成] 使用 Monaco Editor 替换 textarea
 * - [待完成] 接入后端 Docker 沙箱 fallback（需要第三方库时）
 * - [待完成] 保存运行历史与错误模式
 */

let pyodideInstance: any = null

export function PyodideSandbox() {
  const storeCode = useSandboxStore((s) => s.code)
  const [code, setCode] = useState(storeCode)
  const [output, setOutput] = useState('')
  const [loading, setLoading] = useState(true)
  const [running, setRunning] = useState(false)

  useEffect(() => {
    setCode(storeCode)
  }, [storeCode])

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

  const runCode = async () => {
    if (!pyodideInstance) return
    setRunning(true)
    setOutput('')

    const stdout: string[] = []
    const stderr: string[] = []

    pyodideInstance.setStdout({ batched: (text: string) => stdout.push(text) })
    pyodideInstance.setStderr({ batched: (text: string) => stderr.push(text) })

    try {
      await pyodideInstance.runPythonAsync(code)
      setOutput(stdout.join('') || '（无输出）')
    } catch (err: any) {
      setOutput(`错误：${err.message}\n${stderr.join('')}`)
    } finally {
      setRunning(false)
    }
  }

  return (
    <Card className="h-[600px] flex flex-col">
      <CardHeader className="pb-3 flex flex-row items-center justify-between">
        <CardTitle className="text-lg">Python 代码沙箱</CardTitle>
        <div className="flex gap-2">
          <Button variant="outline" size="sm" onClick={() => setCode('')}>
            <RotateCcw className="w-4 h-4 mr-1" /> 清空
          </Button>
          <Button size="sm" onClick={runCode} disabled={loading || running}>
            <Play className="w-4 h-4 mr-1" /> {running ? '运行中' : '运行'}
          </Button>
        </div>
      </CardHeader>
      <CardContent className="flex-1 flex flex-col gap-4">
        {loading ? (
          <div className="flex-1 flex items-center justify-center text-muted-foreground">
            正在加载 Pyodide...
          </div>
        ) : (
          <>
            <textarea
              className="flex-1 font-mono text-sm p-4 rounded-lg border bg-slate-950 text-slate-50 resize-none focus:outline-none focus:ring-2 focus:ring-ring"
              value={code}
              onChange={(e) => setCode(e.target.value)}
              spellCheck={false}
            />
            <div className="h-40 font-mono text-sm p-4 rounded-lg border bg-muted overflow-auto whitespace-pre-wrap">
              {output || '输出区域'}
            </div>
          </>
        )}
      </CardContent>
    </Card>
  )
}
