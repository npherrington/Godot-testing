// The spectrum at the cursor, in multiples of the note's frequency: measured by FFT from
// the rendered samples, and (with no feedback) predicted by the Bessel functions.

import { useCallback, useMemo, useState } from 'react'
import { axes, niceTicks, polyline, useCanvas, type Box, type Colors } from './canvas'
import { PlotFrame, type Tip } from './PlotFrame'
import { fmLines, measure, type Line } from '@/synth/spectrum'

const PAD = { l: 40, r: 10, t: 8, b: 22 }
const FLOOR = -72

const db = (a: number) => Math.max(FLOOR, 20 * Math.log10(Math.max(a, 1e-9)))

export function SpectrumPlot({
  samples,
  sr,
  freq,
  cursor,
  index,
  ratio,
  feedback,
  gain,
  height = 190,
}: {
  samples: Float64Array
  sr: number
  freq: number
  cursor: number
  /** I at the cursor */
  index: number
  ratio: number
  feedback: number
  /** level × velocity × A at the cursor */
  gain: number
  height?: number
}) {
  const [hover, setHover] = useState<Tip | null>(null)
  const maxH = Math.max(4, Math.min(24, sr / 2 / freq))
  // A window centred on the cursor: 46 ms, or 93 ms for low notes that need finer bins.
  const size = freq >= 100 ? 2048 : 4096
  const n0 = Math.min(samples.length - 1, Math.floor(cursor * sr)) - size / 2
  const spec = useMemo(() => measure(samples, n0, size), [samples, n0, size])
  const predicted = useMemo<Line[]>(
    () => (feedback === 0 ? fmLines(index, ratio, maxH, gain) : []),
    [feedback, index, ratio, maxH, gain],
  )
  const binHz = sr / size

  const draw = useCallback(
    (ctx: CanvasRenderingContext2D, w: number, h: number, c: Colors) => {
      const box: Box = { x: PAD.l, y: PAD.t, w: w - PAD.l - PAD.r, h: h - PAD.t - PAD.b }
      const sx = (harm: number) => box.x + (harm / maxH) * box.w
      const sy = (d: number) => box.y + ((0 - d) / (0 - FLOOR)) * box.h
      const xt = niceTicks(0, maxH, Math.max(2, Math.floor(box.w / 45)))
      const yt = niceTicks(FLOOR, 0, 4)
      axes(ctx, box, c, xt, yt, sx, sy, (v) => `${+v.toFixed(1)}f`, (v) => `${v}dB`)
      const last = Math.min(spec.length - 1, Math.ceil((maxH * freq) / binHz))
      polyline(
        ctx,
        last + 1,
        (k) => sx((k * binHz) / freq),
        (k) => sy(db(spec[k])),
        c.series1,
        1.5,
      )
      for (const l of predicted) {
        const x = sx(l.harmonic)
        const y = sy(db(l.amp))
        ctx.beginPath()
        ctx.arc(x, y, 4, 0, 2 * Math.PI)
        ctx.fillStyle = c.series2
        ctx.fill()
        ctx.lineWidth = 2
        ctx.strokeStyle = c.surface
        ctx.stroke()
      }
    },
    [spec, predicted, maxH, freq, binHz],
  )
  const { ref, width } = useCanvas(draw, height)

  const measuredAt = (harm: number) => {
    const k = Math.round((harm * freq) / binHz)
    let best = 0
    for (let j = Math.max(0, k - 2); j <= Math.min(spec.length - 1, k + 2); j++) best = Math.max(best, spec[j])
    return db(best)
  }

  return (
    <PlotFrame
      title={`Spectrum at t = ${cursor.toFixed(3)} s`}
      legend={[
        { color: 'var(--series-1)', label: 'measured (FFT)' },
        ...(predicted.length ? [{ color: 'var(--series-2)', label: 'predicted: |Jₖ(I)| at (1 + k·r)·f' }] : []),
      ]}
      caption={
        feedback === 0
          ? `I = ${index.toFixed(2)}. Each dot is a sideband k, at (1 + k·r)·f, as loud as |Jₖ(I)|. More index spreads energy to higher k: a brighter sound. The FFT covers the ${Math.round((size / sr) * 1000)} ms around the cursor, so it smears fast changes.`
          : 'Feedback is on, so the Bessel prediction no longer applies (the modulator is no longer a sine). The FFT still shows the truth.'
      }
      tip={hover}
    >
      <canvas
        ref={ref}
        className="block touch-none"
        role="img"
        aria-label="Spectrum at the cursor"
        onPointerMove={(e) => {
          const rect = e.currentTarget.getBoundingClientRect()
          const x = e.clientX - rect.left
          const y = e.clientY - rect.top
          const harm = ((x - PAD.l) / (width - PAD.l - PAD.r)) * maxH
          if (harm < 0 || harm > maxH) return setHover(null)
          const pxPerH = (width - PAD.l - PAD.r) / maxH
          const near = predicted.find((l) => Math.abs(l.harmonic - harm) * pxPerH < 8)
          const flip = x > width / 2
          if (near) {
            const ks = near.ks.map((k) => `k=${k}`).join(', ')
            setHover({
              x,
              y,
              flip,
              text: (
                <>
                  {+near.harmonic.toFixed(3)}·f = {(near.harmonic * freq).toFixed(1)} Hz ({ks}) · predicted{' '}
                  {db(near.amp).toFixed(1)} dB · measured {measuredAt(near.harmonic).toFixed(1)} dB
                </>
              ),
            })
          } else {
            setHover({
              x,
              y,
              flip,
              text: (
                <>
                  {harm.toFixed(2)}·f = {(harm * freq).toFixed(0)} Hz · measured {measuredAt(harm).toFixed(1)} dB
                </>
              ),
            })
          }
        }}
        onPointerLeave={() => setHover(null)}
      />
    </PlotFrame>
  )
}
