// Two periods of the note at the cursor: the FM output, and the same note with the
// modulation switched off (I = 0) so you can see how far the modulator bends it.

import { useCallback, useMemo, useState } from 'react'
import { axes, niceTicks, polyline, useCanvas, vline, type Box, type Colors } from './canvas'
import { PlotFrame, type Tip } from './PlotFrame'
import { TAU } from '@/synth/patch'

const PAD = { l: 40, r: 10, t: 8, b: 22 }
const PERIODS = 2

export function WavePlot({
  samples,
  volume,
  gain,
  sr,
  freq,
  cursor,
  height = 170,
}: {
  samples: Float64Array
  volume: Float64Array
  /** level × velocity */
  gain: number
  sr: number
  freq: number
  cursor: number
  height?: number
}) {
  const [hover, setHover] = useState<Tip | null>(null)
  const win = useMemo(() => {
    const n0 = Math.min(samples.length - 1, Math.floor(cursor * sr))
    const len = Math.max(8, Math.round((PERIODS * sr) / freq))
    const n = Math.max(1, Math.min(len, samples.length - n0))
    const y = samples.subarray(n0, n0 + n)
    const ref = new Float64Array(n)
    for (let i = 0; i < n; i++) ref[i] = gain * volume[n0 + i] * Math.sin((TAU * freq * (n0 + i)) / sr)
    let peak = 0.05
    for (let i = 0; i < n; i++) peak = Math.max(peak, Math.abs(y[i]), Math.abs(ref[i]))
    return { n0, n, y, ref, peak: peak * 1.1 }
  }, [samples, volume, gain, sr, freq, cursor])

  const draw = useCallback(
    (ctx: CanvasRenderingContext2D, w: number, h: number, c: Colors) => {
      const box: Box = { x: PAD.l, y: PAD.t, w: w - PAD.l - PAD.r, h: h - PAD.t - PAD.b }
      const ms = (win.n / sr) * 1000
      const sx = (i: number) => box.x + (i / Math.max(1, win.n - 1)) * box.w
      const sy = (v: number) => box.y + box.h / 2 - (v / win.peak) * (box.h / 2)
      const xt = niceTicks(0, ms, Math.max(2, Math.floor(box.w / 70)))
      const yt = niceTicks(-win.peak, win.peak, 4)
      axes(
        ctx,
        box,
        c,
        xt,
        yt,
        (v) => box.x + (v / ms) * box.w,
        sy,
        (v) => `+${+v.toFixed(2)}ms`,
        (v) => `${+v.toFixed(2)}`,
      )
      // one carrier period, marked
      vline(ctx, sx(win.n / PERIODS), box, c.grid, [2, 3])
      polyline(ctx, win.n, sx, (i) => sy(win.ref[i]), c.muted, 1.5, [4, 3])
      polyline(ctx, win.n, sx, (i) => sy(win.y[i]), c.series1, 2)
    },
    [win, sr],
  )
  const { ref, width } = useCanvas(draw, height)

  return (
    <PlotFrame
      title={`Waveform at t = ${cursor.toFixed(3)} s`}
      legend={[
        { color: 'var(--series-1)', label: 'y(t), with FM' },
        { color: 'var(--muted-foreground)', label: 'I = 0, a plain sine', dashed: true },
      ]}
      caption={`Two periods of ${freq.toFixed(1)} Hz. With a whole-number ratio every period repeats; the dotted line marks one.`}
      tip={hover}
    >
      <canvas
        ref={ref}
        className="block touch-none"
        role="img"
        aria-label="Waveform of two periods at the cursor"
        onPointerMove={(e) => {
          const rect = e.currentTarget.getBoundingClientRect()
          const x = e.clientX - rect.left
          const i = Math.round(((x - PAD.l) / (width - PAD.l - PAD.r)) * (win.n - 1))
          if (i < 0 || i >= win.n) return setHover(null)
          setHover({
            x,
            y: e.clientY - rect.top,
            flip: x > width / 2,
            text: (
              <>
                t = {((win.n0 + i) / sr).toFixed(4)} s · y = {win.y[i].toFixed(3)} · sine {win.ref[i].toFixed(3)}
              </>
            ),
          })
        }}
        onPointerLeave={() => setHover(null)}
      />
    </PlotFrame>
  )
}
