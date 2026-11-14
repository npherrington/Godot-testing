// Shared plumbing for the canvas plots: sizing for sharp lines at any pixel ratio,
// theme colours read from CSS variables, and axes.

import { useEffect, useRef, useState } from 'react'

export interface Box {
  x: number
  y: number
  w: number
  h: number
}

export interface Colors {
  series1: string
  series2: string
  series3: string
  text: string
  muted: string
  grid: string
  surface: string
}

function readColors(el: Element): Colors {
  const s = getComputedStyle(el)
  const v = (name: string) => s.getPropertyValue(name).trim()
  return {
    series1: v('--series-1'),
    series2: v('--series-2'),
    series3: v('--series-3'),
    text: v('--foreground'),
    muted: v('--muted-foreground'),
    grid: v('--border'),
    surface: v('--card'),
  }
}

/** Watches the html element's class so plots redraw when the theme flips. */
function useThemeKey(): string {
  const [key, setKey] = useState(() => document.documentElement.className)
  useEffect(() => {
    const obs = new MutationObserver(() => setKey(document.documentElement.className))
    obs.observe(document.documentElement, { attributes: true, attributeFilter: ['class'] })
    return () => obs.disconnect()
  }, [])
  return key
}

export type Draw = (ctx: CanvasRenderingContext2D, w: number, h: number, c: Colors) => void

/** A canvas that fills its parent's width at a fixed height and redraws on any change. */
export function useCanvas(draw: Draw, height: number) {
  const ref = useRef<HTMLCanvasElement>(null)
  const [width, setWidth] = useState(0)
  const theme = useThemeKey()

  useEffect(() => {
    const el = ref.current?.parentElement
    if (!el) return
    const obs = new ResizeObserver(([entry]) => setWidth(Math.floor(entry.contentRect.width)))
    obs.observe(el)
    return () => obs.disconnect()
  }, [])

  useEffect(() => {
    const canvas = ref.current
    if (!canvas || width === 0) return
    const dpr = window.devicePixelRatio || 1
    canvas.width = Math.round(width * dpr)
    canvas.height = Math.round(height * dpr)
    canvas.style.width = `${width}px`
    canvas.style.height = `${height}px`
    const ctx = canvas.getContext('2d')
    if (!ctx) return
    ctx.setTransform(dpr, 0, 0, dpr, 0, 0)
    ctx.clearRect(0, 0, width, height)
    draw(ctx, width, height, readColors(canvas))
  }, [draw, width, height, theme])

  return { ref, width }
}

export const FONT = '10px "JetBrains Mono Variable", monospace'

export function niceTicks(lo: number, hi: number, count: number): number[] {
  const span = hi - lo
  if (!(span > 0)) return [lo]
  const raw = span / count
  const mag = Math.pow(10, Math.floor(Math.log10(raw)))
  const step = [1, 2, 2.5, 5, 10].map((m) => m * mag).find((s) => span / s <= count) ?? 10 * mag
  const out: number[] = []
  for (let v = Math.ceil(lo / step) * step; v <= hi + step * 1e-9; v += step) out.push(Math.abs(v) < step * 1e-9 ? 0 : v)
  return out
}

/** Recessive grid and tick labels. sx and sy map data to pixels. */
export function axes(
  ctx: CanvasRenderingContext2D,
  box: Box,
  c: Colors,
  xs: number[],
  ys: number[],
  sx: (v: number) => number,
  sy: (v: number) => number,
  fx: (v: number) => string,
  fy: (v: number) => string,
): void {
  ctx.save()
  ctx.font = FONT
  ctx.lineWidth = 1
  ctx.strokeStyle = c.grid
  ctx.fillStyle = c.muted
  ctx.textAlign = 'right'
  ctx.textBaseline = 'middle'
  for (const y of ys) {
    const py = Math.round(sy(y)) + 0.5
    ctx.beginPath()
    ctx.moveTo(box.x, py)
    ctx.lineTo(box.x + box.w, py)
    ctx.stroke()
    ctx.fillText(fy(y), box.x - 6, py)
  }
  ctx.textAlign = 'center'
  ctx.textBaseline = 'top'
  for (const x of xs) ctx.fillText(fx(x), sx(x), box.y + box.h + 6)
  ctx.restore()
}

export function polyline(
  ctx: CanvasRenderingContext2D,
  n: number,
  px: (i: number) => number,
  py: (i: number) => number,
  color: string,
  width = 2,
  dash: number[] = [],
): void {
  ctx.save()
  ctx.strokeStyle = color
  ctx.lineWidth = width
  ctx.lineJoin = 'round'
  ctx.setLineDash(dash)
  ctx.beginPath()
  for (let i = 0; i < n; i++) {
    if (i === 0) ctx.moveTo(px(i), py(i))
    else ctx.lineTo(px(i), py(i))
  }
  ctx.stroke()
  ctx.restore()
}

export function vline(ctx: CanvasRenderingContext2D, x: number, box: Box, color: string, dash: number[] = []): void {
  ctx.save()
  ctx.strokeStyle = color
  ctx.lineWidth = 1
  ctx.setLineDash(dash)
  ctx.beginPath()
  ctx.moveTo(Math.round(x) + 0.5, box.y)
  ctx.lineTo(Math.round(x) + 0.5, box.y + box.h)
  ctx.stroke()
  ctx.restore()
}
