// A patch is one FM instrument: everything about the sound except which note is played.
//
//   y(t) = level · velocity · A(t) · sin(2π·f·t + I(t)·m(t))
//   m(t) = sin(2π·r·f·t + β·(m₋₁ + m₋₂)/2)
//
// f is the note's frequency and t the time since the key went down. The patch sets the
// ratio r, the feedback β, the index I(t) and the volume A(t). m₋₁ and m₋₂ are the
// modulator's previous two samples (the Mega Drive's chip averages two the same way).
// The JSON form below is what the app saves and what art/audio/fm.py reads.

import { compile, type Fn2 } from './expr'

export const PATCH_FORMAT = 'fm-patch/1'

/** Volume envelope. Decay and release are times to fall 60 dB, in seconds. */
export interface Envelope {
  attack: number
  decay: number
  sustain: number
  release: number
}

export type IndexSpec =
  | { shape: 'constant'; value: number }
  | { shape: 'decay'; start: number; end: number; tau: number }
  | ({ shape: 'envelope'; peak: number } & Envelope)
  | { shape: 'wobble'; center: number; depth: number; rate: number }
  | { shape: 'formula'; expr: string }

export type IndexShape = IndexSpec['shape']

export interface Patch {
  format: typeof PATCH_FORMAT
  name: string
  ratio: number
  feedback: number
  level: number
  amp: Envelope
  index: IndexSpec
}

export const INDEX_SHAPES: { shape: IndexShape; label: string; formula: string }[] = [
  { shape: 'constant', label: 'Constant', formula: 'I(t) = I₀' },
  { shape: 'decay', label: 'Decay', formula: 'I(t) = I₁ + (I₀ − I₁)·e^(−t/τ)' },
  { shape: 'envelope', label: 'Envelope', formula: 'I(t) = I₀·E(t)' },
  { shape: 'wobble', label: 'Wobble', formula: 'I(t) = I₀ + a·sin(2π·v·t)' },
  { shape: 'formula', label: 'Formula', formula: 'I(t) = your formula' },
]

/** Default parameters for every index shape, so switching shape keeps a sensible sound. */
export const DEFAULT_INDEX: { [S in IndexShape]: Extract<IndexSpec, { shape: S }> } = {
  constant: { shape: 'constant', value: 2 },
  decay: { shape: 'decay', start: 6, end: 1, tau: 0.12 },
  envelope: { shape: 'envelope', peak: 4, attack: 0.01, decay: 0.5, sustain: 0.4, release: 0.3 },
  wobble: { shape: 'wobble', center: 2, depth: 1.5, rate: 6 },
  formula: { shape: 'formula', expr: '4*exp(-6*t) + 0.5*sin(2*pi*5*t)' },
}

export const DEFAULT_PATCH: Patch = {
  format: PATCH_FORMAT,
  name: 'untitled',
  ratio: 1,
  feedback: 0,
  level: 0.8,
  amp: { attack: 0.005, decay: 1.2, sustain: 0.6, release: 0.25 },
  index: DEFAULT_INDEX.decay,
}

// ---------------------------------------------------------------- the maths

export const TAU = 2 * Math.PI
/** 3·ln(10): exp(−K·x/T) falls 60 dB over x = T. */
export const K60 = 6.907755278982138
/** A release has fallen below one 16-bit step (1/32768) after this many release times. */
export const TAIL_RELEASES = 1.505149978319906 // log10(32768) / 3

/** Attack, decay and sustain: the envelope while the key is held. */
export function ads(t: number, e: Envelope): number {
  if (t < e.attack) return t / e.attack
  if (e.decay <= 0) return e.sustain
  return e.sustain + (1 - e.sustain) * Math.exp((-K60 * (t - e.attack)) / e.decay)
}

/** The full envelope. g is when the key was released (Infinity while it's held). */
export function envelope(t: number, e: Envelope, g: number): number {
  if (t < g) return ads(t, e)
  if (e.release <= 0) return 0
  return ads(g, e) * Math.exp((-K60 * (t - g)) / e.release)
}

/** I(t, f, g) for an index spec. Non-finite results (a formula dividing by zero) count as 0. */
export type IndexFn = (t: number, f: number, g: number) => number

export function indexFn(spec: IndexSpec): IndexFn {
  switch (spec.shape) {
    case 'constant': {
      const v = spec.value
      return () => v
    }
    case 'decay': {
      const { start, end, tau } = spec
      if (tau <= 0) return () => end
      return (t) => end + (start - end) * Math.exp(-t / tau)
    }
    case 'envelope': {
      const { peak } = spec
      return (t, _f, g) => peak * envelope(t, spec, g)
    }
    case 'wobble': {
      const { center, depth, rate } = spec
      return (t) => center + depth * Math.sin(TAU * rate * t)
    }
    case 'formula': {
      const fn: Fn2 = compile(spec.expr)
      return (t, f) => {
        const v = fn(t, f)
        return Number.isFinite(v) ? v : 0
      }
    }
  }
}

/** Seconds a note lasts after release before it is silent. */
export function tailSeconds(p: Patch): number {
  return p.amp.release * TAIL_RELEASES
}

// ---------------------------------------------------------------- reading JSON

const num = (v: unknown, fallback: number, lo = -Infinity, hi = Infinity): number =>
  typeof v === 'number' && Number.isFinite(v) ? Math.min(hi, Math.max(lo, v)) : fallback

function readEnvelope(raw: unknown, fallback: Envelope): Envelope {
  const o = (raw ?? {}) as Record<string, unknown>
  return {
    attack: num(o.attack, fallback.attack, 0, 10),
    decay: num(o.decay, fallback.decay, 0, 30),
    sustain: num(o.sustain, fallback.sustain, 0, 1),
    release: num(o.release, fallback.release, 0, 10),
  }
}

function readIndex(raw: unknown): IndexSpec {
  const o = (raw ?? {}) as Record<string, unknown>
  switch (o.shape) {
    case 'constant':
      return { shape: 'constant', value: num(o.value, DEFAULT_INDEX.constant.value) }
    case 'decay': {
      const d = DEFAULT_INDEX.decay
      return { shape: 'decay', start: num(o.start, d.start), end: num(o.end, d.end), tau: num(o.tau, d.tau, 0) }
    }
    case 'envelope': {
      const d = DEFAULT_INDEX.envelope
      return { shape: 'envelope', peak: num(o.peak, d.peak), ...readEnvelope(o, d) }
    }
    case 'wobble': {
      const d = DEFAULT_INDEX.wobble
      return {
        shape: 'wobble',
        center: num(o.center, d.center),
        depth: num(o.depth, d.depth),
        rate: num(o.rate, d.rate, 0),
      }
    }
    case 'formula':
      if (typeof o.expr !== 'string') throw new Error('index.expr must be a string')
      compile(o.expr) // throws ExprError when it doesn't parse
      return { shape: 'formula', expr: o.expr }
    default:
      throw new Error(`unknown index shape ${JSON.stringify(o.shape)}`)
  }
}

/** Check and clean a parsed JSON patch. Throws with a message when it isn't one. */
export function readPatch(raw: unknown): Patch {
  if (typeof raw !== 'object' || raw === null) throw new Error('a patch is a JSON object')
  const o = raw as Record<string, unknown>
  if (o.format !== PATCH_FORMAT) throw new Error(`format must be "${PATCH_FORMAT}"`)
  return {
    format: PATCH_FORMAT,
    name: typeof o.name === 'string' && o.name ? o.name : 'untitled',
    ratio: num(o.ratio, 1, 0.0625, 32),
    feedback: num(o.feedback, 0, 0, 2),
    level: num(o.level, 0.8, 0, 1),
    amp: readEnvelope(o.amp, DEFAULT_PATCH.amp),
    index: readIndex(o.index),
  }
}

/** Patch names become file names: lower case letters, digits and _ only. */
export function slug(name: string): string {
  return (
    name
      .toLowerCase()
      .replace(/[^a-z0-9]+/g, '_')
      .replace(/^_+|_+$/g, '')
      .slice(0, 48) || 'untitled'
  )
}
