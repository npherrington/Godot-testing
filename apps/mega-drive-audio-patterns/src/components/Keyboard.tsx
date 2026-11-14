// Two octaves of piano keys, played by pointer or by the computer keyboard in the
// tracker layout: Z S X D C V G B H N J M , for the lower octave, Q 2 W 3 E R 5 T 6 Y 7 U I
// for the upper one. [ and ] shift the octave.

import { useEffect, useLayoutEffect, useRef } from 'react'
import { CaretLeftIcon, CaretRightIcon } from '@phosphor-icons/react'
import { Button } from '@/components/ui/button'
import { cn } from '@/lib/utils'
import { noteName } from '@/synth/voice'

const LOWER = ['z', 's', 'x', 'd', 'c', 'v', 'g', 'b', 'h', 'n', 'j', 'm', ',']
const UPPER = ['q', '2', 'w', '3', 'e', 'r', '5', 't', '6', 'y', '7', 'u', 'i']
const BLACK = new Set([1, 3, 6, 8, 10])

function keyOffset(key: string): number | null {
  const lo = LOWER.indexOf(key)
  if (lo >= 0) return lo
  const up = UPPER.indexOf(key)
  return up >= 0 ? 12 + up : null
}

function typing(target: EventTarget | null): boolean {
  const el = target as HTMLElement | null
  return !!el && (el.isContentEditable || ['INPUT', 'TEXTAREA', 'SELECT'].includes(el.tagName))
}

export function Keyboard({
  octave,
  onOctave,
  held,
  selected,
  onNoteOn,
  onNoteOff,
}: {
  octave: number
  onOctave: (o: number) => void
  held: ReadonlySet<number>
  selected: number
  onNoteOn: (midi: number) => void
  onNoteOff: (midi: number) => void
}) {
  const base = 12 * (octave + 1) // MIDI of C in this octave
  const down = useRef(new Map<string, number>()) // computer key -> midi it started
  const pointer = useRef<number | null>(null)
  const handlers = useRef({ onNoteOn, onNoteOff, onOctave, octave, base })
  useLayoutEffect(() => {
    handlers.current = { onNoteOn, onNoteOff, onOctave, octave, base }
  })

  useEffect(() => {
    const keydown = (e: KeyboardEvent) => {
      if (e.repeat || e.metaKey || e.ctrlKey || e.altKey || typing(e.target)) return
      const h = handlers.current
      const key = e.key.toLowerCase()
      if (key === '[' || key === ']') {
        h.onOctave(Math.max(0, Math.min(7, h.octave + (key === ']' ? 1 : -1))))
        return
      }
      const off = keyOffset(key)
      if (off === null || down.current.has(key)) return
      e.preventDefault()
      const midi = h.base + off
      down.current.set(key, midi)
      h.onNoteOn(midi)
    }
    const keyup = (e: KeyboardEvent) => {
      const midi = down.current.get(e.key.toLowerCase())
      if (midi === undefined) return
      down.current.delete(e.key.toLowerCase())
      handlers.current.onNoteOff(midi)
    }
    const blur = () => {
      for (const midi of down.current.values()) handlers.current.onNoteOff(midi)
      down.current.clear()
    }
    window.addEventListener('keydown', keydown)
    window.addEventListener('keyup', keyup)
    window.addEventListener('blur', blur)
    return () => {
      window.removeEventListener('keydown', keydown)
      window.removeEventListener('keyup', keyup)
      window.removeEventListener('blur', blur)
    }
  }, [])

  const press = (midi: number) => {
    if (pointer.current !== null) onNoteOff(pointer.current)
    pointer.current = midi
    onNoteOn(midi)
  }
  const lift = () => {
    if (pointer.current !== null) onNoteOff(pointer.current)
    pointer.current = null
  }

  const keys = Array.from({ length: 25 }, (_, i) => base + i)
  const whites = keys.filter((m) => !BLACK.has(m % 12))
  const label = (i: number) => (i < 13 ? LOWER[i] : UPPER[i - 12])

  return (
    <div className="flex flex-col gap-2">
      <div className="flex items-center gap-2 text-[11px] text-muted-foreground">
        <Button variant="outline" size="icon-xs" onClick={() => onOctave(Math.max(0, octave - 1))} aria-label="Octave down">
          <CaretLeftIcon />
        </Button>
        <span className="tabular-nums text-foreground">
          {noteName(base)}–{noteName(base + 24)}
        </span>
        <Button variant="outline" size="icon-xs" onClick={() => onOctave(Math.min(7, octave + 1))} aria-label="Octave up">
          <CaretRightIcon />
        </Button>
        <span className="hidden sm:inline">Click, or type Z–M and Q–I. [ and ] change octave.</span>
      </div>
      <div className="relative h-28 select-none" onPointerUp={lift} onPointerLeave={lift} onPointerCancel={lift}>
        <div className="absolute inset-0 flex">
          {whites.map((m) => (
            <button
              key={m}
              type="button"
              aria-label={noteName(m)}
              onPointerDown={(e) => {
                e.preventDefault()
                press(m)
              }}
              onPointerEnter={(e) => e.buttons & 1 && press(m)}
              className={cn(
                'relative flex flex-1 items-end justify-center border border-r-0 border-border bg-white pb-1.5 text-[10px] text-neutral-500 last:border-r dark:bg-neutral-200',
                held.has(m) && 'bg-[var(--series-1)]! text-white',
                m === selected && !held.has(m) && 'shadow-[inset_0_-3px_0_var(--series-1)]',
              )}
            >
              <span className="flex flex-col items-center leading-tight">
                <span className="uppercase opacity-70">{label(m - base)}</span>
                {m % 12 === 0 && <span>{noteName(m)}</span>}
              </span>
            </button>
          ))}
        </div>
        {keys.map((m, i) => {
          if (!BLACK.has(m % 12)) return null
          const whitesBefore = keys.slice(0, i).filter((k) => !BLACK.has(k % 12)).length
          const left = (whitesBefore / whites.length) * 100
          const w = (100 / whites.length) * 0.62
          return (
            <button
              key={m}
              type="button"
              aria-label={noteName(m)}
              onPointerDown={(e) => {
                e.preventDefault()
                press(m)
              }}
              onPointerEnter={(e) => e.buttons & 1 && press(m)}
              style={{ left: `calc(${left}% - ${w / 2}%)`, width: `${w}%` }}
              className={cn(
                'absolute top-0 z-10 flex h-[62%] items-end justify-center bg-neutral-900 pb-1 text-[9px] text-neutral-400 uppercase ring-1 ring-neutral-700 dark:bg-neutral-950',
                held.has(m) && 'bg-[var(--series-1)]! text-white',
                m === selected && !held.has(m) && 'shadow-[inset_0_-3px_0_var(--series-1)]',
              )}
            >
              {label(i)}
            </button>
          )
        })}
      </div>
    </div>
  )
}
