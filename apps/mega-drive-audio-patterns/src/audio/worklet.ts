// Runs on the audio thread: plays FmVoices for held keys, sample by sample.
// The main thread sends messages (see Msg); nothing comes back.

import type { Patch } from '../synth/patch'
import { FmVoice } from '../synth/voice'

export type Msg =
  | { type: 'patch'; patch: Patch }
  | { type: 'on'; id: string; freq: number; velocity: number }
  | { type: 'off'; id: string }
  | { type: 'allOff' }

const MAX_VOICES = 16

class FmSynth extends AudioWorkletProcessor {
  private patch: Patch | null = null
  private voices = new Map<string, FmVoice>()
  private releasing: FmVoice[] = []

  constructor() {
    super()
    this.port.onmessage = (e: MessageEvent<Msg>) => this.receive(e.data)
  }

  private receive(msg: Msg): void {
    switch (msg.type) {
      case 'patch':
        this.patch = msg.patch
        for (const v of this.voices.values()) v.update(msg.patch)
        for (const v of this.releasing) v.update(msg.patch)
        break
      case 'on': {
        if (!this.patch) return
        this.release(msg.id)
        while (this.voices.size + this.releasing.length >= MAX_VOICES) {
          if (this.releasing.length) this.releasing.shift()
          else {
            const oldest = this.voices.keys().next().value as string
            this.release(oldest)
          }
        }
        this.voices.set(msg.id, new FmVoice(this.patch, msg.freq, msg.velocity, sampleRate))
        break
      }
      case 'off':
        this.release(msg.id)
        break
      case 'allOff':
        for (const id of [...this.voices.keys()]) this.release(id)
        break
    }
  }

  private release(id: string): void {
    const v = this.voices.get(id)
    if (!v) return
    v.release()
    this.voices.delete(id)
    this.releasing.push(v)
  }

  process(_inputs: Float32Array[][], outputs: Float32Array[][]): boolean {
    const out = outputs[0]
    const left = out[0]
    const n = left.length
    left.fill(0)
    for (const v of this.voices.values()) for (let i = 0; i < n; i++) left[i] += v.next()
    for (const v of this.releasing) for (let i = 0; i < n && !v.done; i++) left[i] += v.next()
    this.releasing = this.releasing.filter((v) => !v.done)
    for (let c = 1; c < out.length; c++) out[c].set(left)
    return true
  }
}

registerProcessor('fm-synth', FmSynth)
