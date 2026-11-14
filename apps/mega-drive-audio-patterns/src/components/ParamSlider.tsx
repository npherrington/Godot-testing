// One parameter: a symbol, a name, a slider and a box to type an exact value.
// Times use a log scale so 1 ms and 2 s are both easy to reach; `zero` puts 0 at the
// far left of a log slider.

import { useId, useRef, useState, type ReactNode } from 'react'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Slider } from '@/components/ui/slider'

const STEPS = 1000

export function ParamSlider({
  symbol,
  label,
  value,
  onChange,
  min,
  max,
  step = 0.01,
  log = false,
  zero = false,
  unit = '',
  digits = 2,
  snap,
  hint,
}: {
  symbol: ReactNode
  label: string
  value: number
  onChange: (v: number) => void
  min: number
  max: number
  step?: number
  log?: boolean
  zero?: boolean
  unit?: string
  digits?: number
  /** Round slider moves to this (typed values are kept as typed). */
  snap?: (v: number) => number
  hint?: string
}) {
  const id = useId()
  const toPos = (v: number): number => {
    if (!log) return v
    if (v <= 0) return 0
    const p = Math.log(v / min) / Math.log(max / min)
    return Math.round(Math.min(1, Math.max(0, p)) * STEPS)
  }
  const fromPos = (p: number): number => {
    if (!log) return p
    if (zero && p === 0) return 0
    const v = min * Math.pow(max / min, p / STEPS)
    return Number(v.toPrecision(3))
  }
  // While the box has focus it shows what's being typed; otherwise the value.
  const [draft, setDraft] = useState<string | null>(null)
  const shown = draft ?? value.toFixed(digits)
  const cancelled = useRef(false)

  const commit = () => {
    const v = Number(draft)
    if (!cancelled.current && draft !== null && draft.trim() !== '' && Number.isFinite(v)) {
      const lo = log && zero ? 0 : min
      onChange(Math.max(lo, Math.min(max, v)))
    }
    cancelled.current = false
    setDraft(null)
  }

  return (
    <div className="grid grid-cols-[minmax(0,1fr)_4.5rem] items-center gap-x-3 gap-y-1.5" title={hint}>
      <Label htmlFor={id} className="flex min-w-0 items-baseline gap-2 text-xs font-normal">
        <span className="w-6 shrink-0 font-medium text-foreground">{symbol}</span>
        <span className="truncate text-muted-foreground">{label}</span>
      </Label>
      <div className="flex items-center gap-1">
        <Input
          id={id}
          value={shown}
          inputMode="decimal"
          className="h-6 px-1.5 text-right text-xs tabular-nums"
          onFocus={() => setDraft(shown)}
          onChange={(e) => setDraft(e.target.value)}
          onBlur={commit}
          onKeyDown={(e) => {
            if (e.key === 'Enter') e.currentTarget.blur()
            if (e.key === 'Escape') {
              cancelled.current = true
              e.currentTarget.blur()
            }
          }}
          aria-label={`${label}${unit ? ` (${unit})` : ''}`}
        />
        {unit && <span className="w-3 text-[10px] text-muted-foreground">{unit}</span>}
      </div>
      <Slider
        className="col-span-2"
        min={log ? 0 : min}
        max={log ? STEPS : max}
        step={log ? 1 : step}
        value={[toPos(value)]}
        onValueChange={([p]) => onChange(snap ? snap(fromPos(p)) : fromPos(p))}
        aria-label={label}
      />
    </div>
  )
}
