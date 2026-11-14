// The AudioWorklet global scope, which TypeScript's DOM library doesn't describe.

declare abstract class AudioWorkletProcessor {
  readonly port: MessagePort
  constructor()
  abstract process(inputs: Float32Array[][], outputs: Float32Array[][], parameters: Record<string, Float32Array>): boolean
}

declare function registerProcessor(name: string, ctor: new () => AudioWorkletProcessor): void

declare const sampleRate: number
