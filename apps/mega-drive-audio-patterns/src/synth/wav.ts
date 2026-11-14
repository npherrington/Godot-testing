// 16-bit mono PCM WAV, the format art/audio's build writes before encoding to Ogg.

export function wavBytes(samples: Int16Array, sr: number): ArrayBuffer {
  const data = samples.length * 2
  const buf = new ArrayBuffer(44 + data)
  const v = new DataView(buf)
  const text = (at: number, s: string) => {
    for (let i = 0; i < s.length; i++) v.setUint8(at + i, s.charCodeAt(i))
  }
  text(0, 'RIFF')
  v.setUint32(4, 36 + data, true)
  text(8, 'WAVE')
  text(12, 'fmt ')
  v.setUint32(16, 16, true) // fmt chunk size
  v.setUint16(20, 1, true) // PCM
  v.setUint16(22, 1, true) // mono
  v.setUint32(24, sr, true)
  v.setUint32(28, sr * 2, true) // bytes per second
  v.setUint16(32, 2, true) // bytes per frame
  v.setUint16(34, 16, true) // bits per sample
  text(36, 'data')
  v.setUint32(40, data, true)
  for (let i = 0; i < samples.length; i++) v.setInt16(44 + i * 2, samples[i], true)
  return buf
}
