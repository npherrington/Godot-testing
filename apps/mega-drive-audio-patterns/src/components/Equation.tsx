// The formula being played, written out, with today's numbers filled in.

import type { Patch } from '@/synth/patch'

const n = (v: number, d = 2) => `${+v.toFixed(d)}`

export function Equation({
  patch,
  freq,
  velocity,
  cursor,
  index,
  volume,
}: {
  patch: Patch
  freq: number
  velocity: number
  cursor: number
  index: number
  volume: number
}) {
  const fb = patch.feedback > 0
  return (
    <div className="flex flex-col gap-1.5 border-b bg-card px-4 py-3 text-xs">
      <div className="flex flex-wrap items-baseline gap-x-6 gap-y-1">
        <code className="text-sm text-foreground">
          y(t) = L·v·<span className="text-[var(--series-1)]">A(t)</span>·sin(2π·f·t +{' '}
          <span className="text-[var(--series-3)]">I(t)</span>·m(t))
        </code>
        <code className="text-muted-foreground">
          m(t) = sin(2π·r·f·t{fb ? ' + β·(m₋₁ + m₋₂)/2' : ''})
        </code>
      </div>
      <div className="flex flex-wrap gap-x-6 gap-y-1 text-muted-foreground">
        <code>
          y(t) = {n(patch.level)}·{n(velocity)}·A(t)·sin(2π·{n(freq, 1)}·t + I(t)·sin(2π·{n(patch.ratio, 3)}·
          {n(freq, 1)}·t{fb ? ` + ${n(patch.feedback)}·(m₋₁ + m₋₂)/2` : ''}))
        </code>
        <code>
          at t = {n(cursor, 3)} s: <span className="text-[var(--series-3)]">I = {n(index, 3)}</span>,{' '}
          <span className="text-[var(--series-1)]">A = {n(volume, 3)}</span>
        </code>
      </div>
    </div>
  )
}
