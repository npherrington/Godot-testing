// A plot's frame: title row with a legend, the canvas, a hover tooltip and a caption.

import type { ReactNode } from 'react'

export interface Tip {
  x: number
  y: number
  text: ReactNode
  /** Show on the left of the pointer (when it's in the right half). */
  flip?: boolean
}

/** A plot frame: title row with an optional legend, the canvas, and a hover tooltip. */
export function PlotFrame({
  title,
  legend,
  caption,
  children,
  tip,
}: {
  title: ReactNode
  legend?: { color: string; label: string; dashed?: boolean }[]
  caption?: ReactNode
  children: ReactNode
  tip?: Tip | null
}) {
  return (
    <figure className="flex min-w-0 flex-col gap-2">
      <figcaption className="flex flex-wrap items-baseline justify-between gap-x-4 gap-y-1">
        <span className="text-xs font-medium">{title}</span>
        {legend && legend.length > 1 && (
          <span className="flex flex-wrap gap-3 text-[11px] text-muted-foreground">
            {legend.map((l) => (
              <span key={l.label} className="flex items-center gap-1.5">
                <svg width="16" height="8" aria-hidden>
                  <line
                    x1="0"
                    y1="4"
                    x2="16"
                    y2="4"
                    stroke={l.color}
                    strokeWidth="2"
                    strokeDasharray={l.dashed ? '3 3' : undefined}
                  />
                </svg>
                {l.label}
              </span>
            ))}
          </span>
        )}
      </figcaption>
      <div className="relative">
        {children}
        {tip && (
          <div
            className="pointer-events-none absolute z-10 rounded-none border bg-popover px-2 py-1 text-[11px] whitespace-nowrap text-popover-foreground shadow-md"
            style={{
              left: tip.x,
              top: tip.y,
              transform: `translate(${tip.flip ? 'calc(-100% - 10px)' : '10px'}, -50%)`,
            }}
          >
            {tip.text}
          </div>
        )}
      </div>
      {caption && <p className="text-[11px] leading-relaxed text-muted-foreground">{caption}</p>}
    </figure>
  )
}
