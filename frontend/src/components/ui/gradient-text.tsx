import * as React from 'react'

import { cn } from '@/lib/utils'

interface GradientTextProps extends React.HTMLAttributes<HTMLSpanElement> {
  children: React.ReactNode
}

const GradientText = React.forwardRef<HTMLSpanElement, GradientTextProps>(
  ({ className, children, ...props }, ref) => {
    return (
      <span
        ref={ref}
        className={cn(
          'bg-gradient-to-r from-indigo-600 via-violet-600 to-indigo-600 bg-clip-text text-transparent',
          className
        )}
        {...props}
      >
        {children}
      </span>
    )
  }
)
GradientText.displayName = 'GradientText'

export { GradientText }
