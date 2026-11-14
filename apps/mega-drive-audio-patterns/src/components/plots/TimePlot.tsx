// A function of time over the whole note: I(t) or A(t). Shows when the key goes up and
// the inspect cursor; click or drag to move the cursor.

import { useCallback, useState, type ReactNode } from 'react'
import { axes, niceTicks, polyline, useCanvas, vline, type Box, type Colors } from './canvas'
import { PlotFrame, type Tip } from './PlotFrame'

const PAD = { l: 40, r: 10, t: 8, b: 22 }

export function TimePlot({
  title,
  caption,
  values,
  sr,
  gateN,
  cursor,
  onCursor,
  color,
  symbol,
  range,
  height = 130,
}: {
  title: ReactNode
  caption?: ReactNode
  values: Float64Array
  sr: number
  gateN: number
  cursor: number
  onCursor: (t: number) => void
  color: 'series1' | 'series2' | 'series3'
  symbol: string
  /** Fixed y range; otherwise fitted to the data. */
  range?: [number, number]
  height?: number
}) {
  const duration = values.length / sr
  const [hover, setHover] = useState<Tip | null>(null)

  const yRange = useCallback((): [number, number] => {
    if (range) return range
    let lo = 0
    let hi = 0
    for (const v of values) {
      if (v < lo) lo = v
      if (v > hi) hi = v
    }
    if (hi - lo < 1) hi = lo + 1
    return [lo, hi + (hi - lo) * 0.08]
  }, [values, range])

  const draw = useCallback(
    (ctx: CanvasRenderingContext2D, w: number, h: number, c: Colors) => {
      const box: Box = { x: PAD.l, y: PAD.t, w: w - PAD.l - PAD.r, h: h - PAD.t - PAD.b }
      const [lo, hi] = yRange()
      const sx = (t: number) => box.x + (t / duration) * box.w
      const sy = (v: number) => box.y + box.h - ((v - lo) / (hi - lo)) * box.h
      const xt = niceTicks(0, duration, Math.max(2, Math.floor(box.w / 70)))
      const yt = niceTicks(lo, hi, 4)
      axes(ctx, box, c, xt, yt, sx, sy, (v) => `${+v.toFixed(3)}s`, (v) => `${+v.toFixed(2)}`)
      // One min and one max per pixel column, so fast wobbles show as a band, not aliasing.
      const cols = Math.max(1, Math.floor(box.w))
      const pts: number[] = []
      for (let col = 0; col < cols; col++) {
        const a = Math.floor((col / cols) * values.length)
        const b = Math.max(a + 1, Math.floor(((col + 1) / cols) * values.length))
        let mn = Infinity
        let mx = -Infinity
        for (let i = a; i < b && i < values.length; i++) {
          if (values[i] < mn) mn = values[i]
          if (values[i] > mx) mx = values[i]
        }
        if (mn === Infinity) continue
        pts.push(col, mn, col, mx)
      }
      polyline(
        ctx,
        pts.length / 2,
        (i) => box.x + pts[i * 2] + 0.5,
        (i) => sy(pts[i * 2 + 1]),
        c[color],
        2,
      )
      if (gateN < values.length) {
        const gx = sx(gateN / sr)
        vline(ctx, gx, box, c.muted, [3, 3])
        ctx.font = '10px "JetBrains Mono Variable", monospace'
        ctx.fillStyle = c.muted
        ctx.textAlign = 'left'
        ctx.textBaseline = 'top'
        ctx.fillText('key up', gx + 4, box.y + 2)
      }
      vline(ctx, sx(cursor), box, c.text)
    },
    [values, sr, gateN, cursor, color, duration, yRange],
  )

  const { ref, width } = useCanvas(draw, height)

  const timeAt = (e: React.PointerEvent<HTMLCanvasElement>) => {
    const rect = e.currentTarget.getBoundingClientRect()
    const x = e.clientX - rect.left
    return { x, y: e.clientY - rect.top, t: Math.min(duration, Math.max(0, ((x - PAD.l) / (width - PAD.l - PAD.r)) * duration)) }
  }

  return (
    <PlotFrame title={title} caption={caption} tip={hover}>
      <canvas
        ref={ref}
        className="block cursor-crosshair touch-none"
        role="img"
        aria-label={`${symbol} over ${duration.toFixed(2)} seconds`}
        onPointerDown={(e) => {
          e.currentTarget.setPointerCapture(e.pointerId)
          onCursor(timeAt(e).t)
        }}
        onPointerMove={(e) => {
          const { x, y, t } = timeAt(e)
          if (e.buttons & 1) onCursor(t)
          const v = values[Math.min(values.length - 1, Math.floor(t * sr))]
          setHover({
            x,
            y,
            flip: x > width / 2,
            text: (
              <>
                t = {t.toFixed(3)} s · {symbol} = {v?.toFixed(3)}
              </>
            ),
          })
        }}
        onPointerLeave={() => setHover(null)}
      />
    </PlotFrame>
  )
}
