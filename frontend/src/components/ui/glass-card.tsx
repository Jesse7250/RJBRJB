import { motion } from 'framer-motion'
import * as React from 'react'

import { cn } from '@/lib/utils'

interface GlassCardProps extends React.ComponentPropsWithoutRef<typeof motion.div> {
  delay?: number
  hover?: boolean
  glow?: boolean
}

const GlassCard = React.forwardRef<HTMLDivElement, GlassCardProps>(
  ({ className, children, delay = 0, hover = true, glow = false, ...props }, ref) => {
    return (
      <motion.div
        ref={ref}
        initial={{ opacity: 0, y: 16 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{
          duration: 0.45,
          delay,
          ease: [0.16, 1, 0.3, 1],
        }}
        className={cn(
          'rounded-2xl border border-white/60 bg-white/80 backdrop-blur-xl shadow-soft',
          hover && 'transition-all duration-200 hover:-translate-y-0.5 hover:shadow-hover',
          glow && 'ring-1 ring-indigo-500/10',
          className
        )}
        {...props}
      >
        {children}
      </motion.div>
    )
  }
)
GlassCard.displayName = 'GlassCard'

export { GlassCard }
