// One sounding note. The same code runs live in the AudioWorklet and offline for the
// plots and WAV export, and art/audio/fm.py repeats it line for line, so all three
// produce the same samples. Keep the arithmetic in the same order as fm.py.

import { envelope, indexFn, tailSeconds, TAU, type Envelope, type IndexFn, type Patch } from './patch'

export class FmVoice {
  readonly freq: number
  private readonly sr: number
  private readonly velocity: number
  private ratio = 1
  private beta = 0
  private amp = 0
  private env!: Envelope
  private index!: IndexFn
  private tailN = 0
  private n = 0
  private m1 = 0
  private m2 = 0
  private gateN = Infinity
  private g = Infinity

  constructor(patch: Patch, freq: number, velocity: number, sr: number) {
    this.freq = freq
    this.sr = sr
    this.velocity = velocity
    this.update(patch)
  }

  /** Switch to a changed patch mid-note (the live sliders), keeping time and phase. */
  update(patch: Patch): void {
    this.ratio = patch.ratio
    this.beta = patch.feedback
    this.amp = patch.level * this.velocity
    this.env = patch.amp
    this.index = indexFn(patch.index)
    this.tailN = Math.ceil(tailSeconds(patch) * this.sr)
  }

  /** Let go of the key: the next sample is the first of the release. */
  release(): void {
    if (this.gateN === Infinity) {
      this.gateN = this.n
      this.g = this.n / this.sr
    }
  }

  get released(): boolean {
    return this.gateN !== Infinity
  }

  /** True once the release has faded below one 16-bit step. */
  get done(): boolean {
    return this.n >= this.gateN + this.tailN
  }

  next(): number {
    const t = this.n / this.sr
    const f = this.freq
    const i = this.index(t, f, this.g)
    const m = Math.sin(TAU * this.ratio * f * t + this.beta * (this.m1 + this.m2) * 0.5)
    this.m2 = this.m1
    this.m1 = m
    this.n++
    return this.amp * envelope(t, this.env, this.g) * Math.sin(TAU * f * t + i * m)
  }
}

export interface Render {
  /** The samples, at most `limit` of them. */
  samples: Float64Array
  /** The index I(t) and volume A(t) at every sample, for the plots. */
  index: Float64Array
  volume: Float64Array
  sr: number
  gateN: number
}

/** Play a note held for gateN samples, then released, to the end of its release. */
export function renderNote(
  patch: Patch,
  freq: number,
  gateN: number,
  velocity = 1,
  sr = 44100,
  limit = Infinity,
): Render {
  const voice = new FmVoice(patch, freq, velocity, sr)
  const total = Math.min(limit, gateN + Math.ceil(tailSeconds(patch) * sr))
  const samples = new Float64Array(total)
  const index = new Float64Array(total)
  const volume = new Float64Array(total)
  const ix = indexFn(patch.index)
  const g = gateN / sr
  for (let n = 0; n < total; n++) {
    if (n === gateN) voice.release()
    const t = n / sr
    const gt = n < gateN ? Infinity : g
    index[n] = ix(t, freq, gt)
    volume[n] = envelope(t, patch.amp, gt)
    samples[n] = voice.next()
  }
  return { samples, index, volume, sr, gateN }
}

/** Float samples to 16-bit integers: clip to ±1, scale by 32767, round half up. */
export function toInt16(x: ArrayLike<number>): Int16Array {
  const out = new Int16Array(x.length)
  for (let n = 0; n < x.length; n++) {
    const v = Math.max(-1, Math.min(1, x[n]))
    out[n] = Math.floor(v * 32767 + 0.5)
  }
  return out
}

/** Equal temperament, A4 = MIDI 69 = 440 Hz. */
export function midiToHz(midi: number): number {
  return 440 * Math.pow(2, (midi - 69) / 12)
}

const NAMES = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B']

export function noteName(midi: number): string {
  return `${NAMES[midi % 12]}${Math.floor(midi / 12) - 1}`
}
