import { describe, expect, it } from 'vitest'
import reference from './__fixtures__/python_reference.json'
import { compile, ExprError } from './expr'
import { envelope, readPatch, type Envelope } from './patch'
import { PRESETS } from './presets'
import { besselJ, fmLines, measure } from './spectrum'
import { renderNote, toInt16 } from './voice'
import { wavBytes } from './wav'

describe('formulas', () => {
  const at = (src: string, t = 0.5, f = 3) => compile(src)(t, f)

  it('follows maths precedence', () => {
    expect(at('-t^2')).toBe(-0.25)
    expect(at('2^-1')).toBe(0.5)
    expect(at('2^3^2')).toBe(512)
    expect(at('2**3')).toBe(8)
    expect(at('1 + 2 * 3 - 4 / 2')).toBe(5)
    expect(at('-(1 + 2) * +3')).toBe(-9)
  })

  it('knows t, f, the constants and the functions', () => {
    expect(at('t*f')).toBe(1.5)
    expect(at('pi')).toBe(Math.PI)
    expect(at('e')).toBe(Math.E)
    expect(at('max(t, f, 7) + min(t, f) + abs(-2) + floor(2.7) + sqrt(16)')).toBe(7 + 0.5 + 2 + 2 + 4)
    expect(at('exp(0) + log(1) + sin(0) + cos(0) + tan(0)')).toBe(2)
    expect(at('1.5e2 + .5')).toBe(150.5)
  })

  it('rejects anything else, saying where', () => {
    const bad: [string, RegExp][] = [
      ['', /empty/],
      ['2t', /unexpected "t"/],
      ['x + 1', /unknown name "x"/],
      ['sin', /needs brackets/],
      ['sin(1, 2)', /one argument/],
      ['max(1)', /two or more/],
      ['alert(1)', /unknown function/],
      ['(1 + 2', /expected "\)"/],
      ['t; 1', /unexpected ";"/],
      ['t > 1', /unexpected ">"/],
    ]
    for (const [src, msg] of bad) {
      expect(() => compile(src), src).toThrow(ExprError)
      expect(() => compile(src), src).toThrow(msg)
    }
  })
})

describe('envelope', () => {
  const e: Envelope = { attack: 0.1, decay: 0.5, sustain: 0.5, release: 0.2 }

  it('ramps up, falls 60 dB of the way to sustain over the decay, then releases', () => {
    expect(envelope(0, e, Infinity)).toBe(0)
    expect(envelope(0.05, e, Infinity)).toBeCloseTo(0.5)
    expect(envelope(0.1, e, Infinity)).toBe(1)
    expect(envelope(0.6, e, Infinity)).toBeCloseTo(0.5 + 0.5 * 0.001, 9)
    expect(envelope(1.2, e, 1.0)).toBeCloseTo(envelope(1.0, e, Infinity) * 0.001, 9)
  })
})

describe('Bessel functions', () => {
  it('match known values', () => {
    // Abramowitz and Stegun, table 9.1
    const J = besselJ(1, 3)
    expect(J[0]).toBeCloseTo(0.7651976866, 9)
    expect(J[1]).toBeCloseTo(0.4400505857, 9)
    expect(J[2]).toBeCloseTo(0.1149034849, 9)
    expect(besselJ(10, 0)[0]).toBeCloseTo(-0.2459357645, 9)
    expect(besselJ(-1, 1)[1]).toBeCloseTo(-0.4400505857, 9)
  })

  it('predict the measured FM spectrum', () => {
    // No feedback and a constant index: the rendered note's FFT should show lines at
    // (1 + k·r)·f with heights |Jₖ(I)|.
    const sr = 44100
    const size = 8192
    const f = (sr / size) * 40 // exactly on an FFT bin
    for (const [ratio, index] of [
      [1, 2],
      [2, 1.5],
      [3, 4],
    ]) {
      const patch = readPatch({
        format: 'fm-patch/1',
        ratio,
        level: 1,
        amp: { attack: 0, decay: 0, sustain: 1, release: 0 },
        index: { shape: 'constant', value: index },
      })
      const { samples } = renderNote(patch, f, size * 2, 1, sr)
      const spec = measure(samples, size, size)
      for (const line of fmLines(index, ratio, 12)) {
        expect(spec[Math.round(line.harmonic * 40)], `r=${ratio} I=${index} h=${line.harmonic}`).toBeCloseTo(
          line.amp,
          3,
        )
      }
    }
  })
})

describe('the Python twin', () => {
  // art/audio/fm.py rendered these cases (mise run fixtures). Every sample must agree to
  // within one 16-bit step: the two only differ where JavaScript's and C's sin, exp and
  // pow round their last bit differently.
  for (const c of reference.cases) {
    it(c.label, () => {
      const bytes = Uint8Array.from(atob(c.int16le), (ch) => ch.charCodeAt(0))
      const want = new Int16Array(bytes.buffer)
      const got = toInt16(renderNote(readPatch(c.patch), c.freq, c.gateN, c.velocity, c.sr, c.limit).samples)
      expect(got.length).toBe(want.length)
      let worst = 0
      for (let n = 0; n < want.length; n++) worst = Math.max(worst, Math.abs(got[n] - want[n]))
      expect(worst).toBeLessThanOrEqual(1)
    })
  }

  it('covers every preset', () => {
    for (const p of PRESETS) expect(reference.cases.some((c) => c.patch.name === p.name), p.name).toBe(true)
  })
})

describe('presets and export', () => {
  it('are valid patches with distinct names', () => {
    expect(new Set(PRESETS.map((p) => p.name)).size).toBe(PRESETS.length)
    for (const p of PRESETS) expect(readPatch(p)).toEqual(p)
  })

  it('end in silence and never clip', () => {
    for (const p of PRESETS) {
      const { samples } = renderNote(p, 220, 22050)
      expect(Math.abs(samples[samples.length - 1]), p.name).toBeLessThan(1 / 32768)
      expect(samples.reduce((m, v) => Math.max(m, Math.abs(v)), 0), p.name).toBeLessThanOrEqual(1)
    }
  })

  it('writes a 16-bit mono WAV', () => {
    const v = new DataView(wavBytes(new Int16Array([0, 32767, -32768]), 44100))
    expect(v.byteLength).toBe(50)
    expect(v.getUint16(22, true)).toBe(1)
    expect(v.getUint16(34, true)).toBe(16)
    expect(v.getInt16(46, true)).toBe(32767)
    expect(v.getInt16(48, true)).toBe(-32768)
  })
})
