import { Check, Loader2 } from 'lucide-react'
import { motion } from 'framer-motion'
import * as React from 'react'

import { cn } from '@/lib/utils'

interface Step {
  key: string
  label: string
  icon: React.ElementType
}

interface StepperProps {
  steps: Step[]
  activeIndex: number
  progress: number
}

export function Stepper({ steps, activeIndex, progress }: StepperProps) {
  return (
    <div className="w-full">
      <div className="relative mb-4 flex items-center justify-between">
        <div className="absolute left-0 right-0 top-1/2 h-1 -translate-y-1/2 rounded-full bg-slate-100" />
        <motion.div
          className="absolute left-0 top-1/2 h-1 -translate-y-1/2 rounded-full bg-gradient-to-r from-indigo-500 to-violet-500"
          initial={{ width: '0%' }}
          animate={{ width: `${progress}%` }}
          transition={{ duration: 0.4, ease: [0.16, 1, 0.3, 1] }}
        />
        {steps.map((step, idx) => {
          const Icon = step.icon
          const completed = idx < activeIndex
          const active = idx === activeIndex

          return (
            <div key={step.key} className="relative z-10 flex flex-col items-center gap-2">
              <motion.div
                initial={false}
                animate={{
                  scale: active ? 1.1 : 1,
                }}
                className={cn(
                  'flex h-8 w-8 items-center justify-center rounded-full border-2 text-xs font-semibold transition-colors',
                  completed
                    ? 'border-indigo-500 bg-indigo-500 text-white'
                    : active
                    ? 'border-indigo-500 bg-white text-indigo-600'
                    : 'border-slate-200 bg-white text-slate-400'
                )}
              >
                {completed ? (
                  <Check className="h-4 w-4" />
                ) : active ? (
                  <Loader2 className="h-4 w-4 animate-spin" />
                ) : (
                  <Icon className="h-3.5 w-3.5" />
                )}
              </motion.div>
              <span
                className={cn(
                  'text-[10px] font-medium',
                  completed || active ? 'text-indigo-700' : 'text-slate-400'
                )}
              >
                {step.label}
              </span>
            </div>
          )
        })}
      </div>
    </div>
  )
}
