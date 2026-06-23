import { create } from 'zustand'

interface SandboxState {
  code: string
  setCode: (code: string) => void
}

export const useSandboxStore = create<SandboxState>((set) => ({
  code: '# 在这里输入 Python 代码\nprint("Hello, Python!")',
  setCode: (code) => set({ code }),
}))
