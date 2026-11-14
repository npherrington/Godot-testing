// The browser side of the sound: one AudioContext, the FM worklet for live keys, and
// plain buffer playback for rendered notes. Browsers only allow audio after a click or
// key press, so everything starts lazily on the first one.

import type { Patch } from '../synth/patch'
import type { Msg } from './worklet'
import workletUrl from './worklet.ts?worker&url'

let ctx: AudioContext | null = null
let node: AudioWorkletNode | null = null
let master: GainNode | null = null
let starting: Promise<void> | null = null
let current: Patch | null = null
let buffer: AudioBufferSourceNode | null = null

function send(msg: Msg): void {
  node?.port.postMessage(msg)
}

/** Create or resume the audio graph. Call from a user gesture. */
export function start(): Promise<void> {
  if (ctx && node) return ctx.state === 'running' ? Promise.resolve() : ctx.resume()
  starting ??= (async () => {
    ctx = new AudioContext({ latencyHint: 'interactive' })
    await ctx.audioWorklet.addModule(workletUrl)
    master = new GainNode(ctx, { gain: 0.8 })
    master.connect(ctx.destination)
    node = new AudioWorkletNode(ctx, 'fm-synth', { numberOfInputs: 0, outputChannelCount: [2] })
    node.connect(master)
    if (current) send({ type: 'patch', patch: current })
    await ctx.resume()
  })()
  return starting
}

export function setPatch(patch: Patch): void {
  current = patch
  send({ type: 'patch', patch })
}

export async function noteOn(id: string, freq: number, velocity = 1): Promise<void> {
  await start()
  send({ type: 'on', id, freq, velocity })
}

export function noteOff(id: string): void {
  send({ type: 'off', id })
}

export function allOff(): void {
  send({ type: 'allOff' })
}

/** Play rendered samples exactly as the plots show them. */
export async function playSamples(samples: Float64Array, sr: number): Promise<void> {
  await start()
  if (!ctx || !master) return
  buffer?.stop()
  const buf = ctx.createBuffer(1, samples.length, sr)
  buf.getChannelData(0).set(samples)
  buffer = new AudioBufferSourceNode(ctx, { buffer: buf })
  buffer.connect(master)
  buffer.start()
}

export function audioRate(): number | null {
  return ctx?.sampleRate ?? null
}
