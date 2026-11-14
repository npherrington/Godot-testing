// The two ways the app shows a spectrum: predicted by the maths, and measured by FFT.
//
// Prediction: with no feedback, sin(2π·f·t + I·sin(2π·r·f·t)) is exactly
//   Σₖ Jₖ(I) · sin(2π·(1 + k·r)·f·t)     for every whole number k
// so there is a line at (1 + k·r) times the note's frequency with height |Jₖ(I)|, where
// Jₖ is the Bessel function of the first kind. A negative frequency folds back to
// positive with its sign flipped, since sin(−x) = −sin(x).

/** J₀(x) … J_K(x), by Miller's backward recurrence (stable for any x). */
export function besselJ(x: number, K: number): Float64Array {
  const out = new Float64Array(K + 1)
  if (x === 0) {
    out[0] = 1
    return out
  }
  const ax = Math.abs(x)
  const top = Math.max(K, ax)
  const N = 2 * Math.ceil((top + 16 + Math.sqrt(40 * top)) / 2)
  const J = new Float64Array(N + 2)
  J[N] = 1
  for (let k = N; k > 0; k--) {
    J[k - 1] = ((2 * k) / ax) * J[k] - J[k + 1]
    if (Math.abs(J[k - 1]) > 1e200) for (let j = k - 1; j <= N; j++) J[j] *= 1e-200
  }
  // J₀ + 2·(J₂ + J₄ + …) = 1
  let norm = J[0]
  for (let k = 2; k <= N; k += 2) norm += 2 * J[k]
  for (let k = 0; k <= K; k++) {
    const v = J[k] / norm
    out[k] = x < 0 && k % 2 === 1 ? -v : v
  }
  return out
}

export interface Line {
  /** Frequency in multiples of the note's frequency. */
  harmonic: number
  /** Amplitude (1 is a full-scale sine). */
  amp: number
  /** The sideband numbers k that land on this frequency. */
  ks: number[]
}

/** The predicted spectrum of the FM formula at one moment, lines up to maxHarmonic. */
export function fmLines(index: number, ratio: number, maxHarmonic: number, gain = 1): Line[] {
  const kMax = Math.ceil((maxHarmonic + 1) / ratio) + 1
  const J = besselJ(index, kMax)
  const lines = new Map<number, { a: number; ks: number[] }>()
  const add = (h: number, a: number, k: number) => {
    const key = Math.round(h * 1e6) / 1e6
    const line = lines.get(key) ?? { a: 0, ks: [] }
    line.a += a
    line.ks.push(k)
    lines.set(key, line)
  }
  for (let k = -kMax; k <= kMax; k++) {
    // J₋ₖ(I) = (−1)ᵏ·Jₖ(I)
    const jk = k >= 0 ? J[k] : J[-k] * (k % 2 === 0 ? 1 : -1)
    const h = 1 + k * ratio
    if (h >= 0) add(h, jk, k)
    else add(-h, -jk, k)
  }
  return [...lines]
    .map(([harmonic, { a, ks }]) => ({ harmonic, amp: Math.abs(a) * gain, ks }))
    .filter((l) => l.harmonic <= maxHarmonic && l.amp > 1e-5 && l.harmonic > 0)
    .sort((a, b) => a.harmonic - b.harmonic)
}

/** In-place radix-2 FFT. re and im have the same power-of-two length. */
export function fft(re: Float64Array, im: Float64Array): void {
  const n = re.length
  for (let i = 1, j = 0; i < n; i++) {
    let bit = n >> 1
    for (; j & bit; bit >>= 1) j ^= bit
    j ^= bit
    if (i < j) {
      ;[re[i], re[j]] = [re[j], re[i]]
      ;[im[i], im[j]] = [im[j], im[i]]
    }
  }
  for (let len = 2; len <= n; len <<= 1) {
    const ang = (-2 * Math.PI) / len
    const wr = Math.cos(ang)
    const wi = Math.sin(ang)
    for (let i = 0; i < n; i += len) {
      let cr = 1
      let ci = 0
      for (let k = 0; k < len / 2; k++) {
        const a = i + k
        const b = a + len / 2
        const tr = re[b] * cr - im[b] * ci
        const ti = re[b] * ci + im[b] * cr
        re[b] = re[a] - tr
        im[b] = im[a] - ti
        re[a] += tr
        im[a] += ti
        const nr = cr * wr - ci * wi
        ci = cr * wi + ci * wr
        cr = nr
      }
    }
  }
}

/**
 * Amplitude spectrum of `size` samples starting at `start`, Hann windowed and scaled so a
 * sine of amplitude a peaks at a. Bin k is k·sr/size Hz. Samples past the end count as 0.
 */
export function measure(x: ArrayLike<number>, start: number, size: number): Float64Array {
  const re = new Float64Array(size)
  const im = new Float64Array(size)
  for (let i = 0; i < size; i++) {
    const w = 0.5 - 0.5 * Math.cos((2 * Math.PI * i) / size)
    const v = start + i < x.length && start + i >= 0 ? x[start + i] : 0
    re[i] = v * w
  }
  fft(re, im)
  const out = new Float64Array(size / 2 + 1)
  for (let k = 0; k <= size / 2; k++) out[k] = (4 * Math.hypot(re[k], im[k])) / size
  return out
}
