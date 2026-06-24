/**
 * 需求：代码沙箱全局状态。
 * 功能：
 *   - 维护当前沙箱代码，支持从 ChatPanel / ResourceViewer 一键写入。
 * TODO:
 *  - [已完成] 代码写入与读取
 *  - [待完成] 多文件 tab、运行状态共享
 */
import { create } from 'zustand'

interface SandboxState {
  code: string
  setCode: (code: string) => void
}

export const useSandboxStore = create<SandboxState>((set) => ({
  code: '# 在这里输入 Python 代码\nprint("Hello, Python!")',
  setCode: (code) => set({ code }),
}))
