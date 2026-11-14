"""Pure-stdlib DSP building blocks for the dungeon audio synth.

Signals are mono lists (or array('d')) of floats at SR. Stereo is a (left, right)
pair. Every random source takes an explicit random.Random so builds are repeatable.
Nothing in this module touches the disk.
"""

import math
from array import array

SR = 44100
TAU = 2.0 * math.pi


# ---------------------------------------------------------------- basics

def ns(seconds):
    """Seconds -> whole samples."""
    return int(round(seconds * SR))


def zeros(n):
    return [0.0] * n


def buf(n):
    """A zeroed array('d'); much lighter than a list for long buses."""
    return array('d', bytes(8 * n))


_PC = {'C': 0, 'D': 2, 'E': 4, 'F': 5, 'G': 7, 'A': 9, 'B': 11}


def note(name):
    """'C#4', 'Bb3', 'D5' -> MIDI number (C4 = 60, A4 = 69)."""
    i, acc = 1, 0
    while i < len(name) and name[i] in '#b':
        acc += 1 if name[i] == '#' else -1
        i += 1
    return 12 * (int(name[i:]) + 1) + _PC[name[0].upper()] + acc


def hz(midi):
    return 440.0 * 2.0 ** ((midi - 69) / 12.0)


def cents(c):
    return 2.0 ** (c / 1200.0)


def as_list(v, n):
    return v if isinstance(v, (list, array)) else [float(v)] * n


# ---------------------------------------------------------------- control curves

def curve(n, points, exp=False):
    """Piecewise curve from [(t_seconds, value), ...]. Holds the end values.
    exp=True interpolates in the log domain (pitch, cutoff); values must be > 0."""
    pts = [(ns(t), (math.log(v) if exp else v)) for t, v in points]
    out = [0.0] * n
    j = 0
    for i in range(n):
        while j < len(pts) - 1 and i >= pts[j + 1][0]:
            j += 1
        t0, v0 = pts[j]
        if j == len(pts) - 1 or i < t0:
            v = v0 if i >= t0 else pts[0][1]
        else:
            t1, v1 = pts[j + 1]
            v = v0 + (v1 - v0) * (i - t0) / max(1, t1 - t0)
        out[i] = v
    if exp:
        e = math.exp
        out = [e(v) for v in out]
    return out


def vibrato(n, base, rate=5.5, depth_cents=12.0, delay=0.12, ramp=0.25, phase=0.0):
    """Frequency list with a delayed, ramped-in sine vibrato."""
    out = [0.0] * n
    sin = math.sin
    d0, rr = ns(delay), max(1, ns(ramp))
    w = TAU * rate / SR
    k = depth_cents / 1200.0 * math.log(2.0)
    e = math.exp
    for i in range(n):
        if i < d0:
            out[i] = base
        else:
            amt = min(1.0, (i - d0) / rr)
            out[i] = base * e(k * amt * sin(phase + w * (i - d0)))
    return out


def smooth_random(n, rate, rng, lo=-1.0, hi=1.0, wrap=False):
    """Cosine-interpolated random walk between points `rate` per second.
    wrap=True makes the curve periodic over n samples (for loops)."""
    seg = max(2, int(SR / rate))
    k = max(1, round(n / seg)) if wrap else n // seg + 2
    pts = [rng.uniform(lo, hi) for _ in range(k)]
    seg_len = n / k if wrap else seg
    out = [0.0] * n
    cos = math.cos
    for i in range(n):
        x = i / seg_len
        j = int(x)
        f = x - j
        a = pts[j % k]
        b = pts[(j + 1) % k]
        m = (1.0 - cos(math.pi * f)) * 0.5
        out[i] = a + (b - a) * m
    return out


# ---------------------------------------------------------------- oscillators

def sine(n, freq, phase=0.0):
    out = [0.0] * n
    sin = math.sin
    if not isinstance(freq, (list, array)):
        w = TAU * freq / SR
        for i in range(n):
            out[i] = sin(phase + w * i)
        return out
    p = phase
    k = TAU / SR
    for i in range(n):
        out[i] = sin(p)
        p += freq[i] * k
        if p > TAU:
            p -= TAU
    return out


def saw(n, freq, phase=0.0):
    """Band-limited (PolyBLEP) sawtooth."""
    fr = as_list(freq, n)
    out = [0.0] * n
    p = phase % 1.0
    k = 1.0 / SR
    for i in range(n):
        dt = fr[i] * k
        v = 2.0 * p - 1.0
        if p < dt:
            x = p / dt
            v -= x + x - x * x - 1.0
        elif p > 1.0 - dt:
            x = (p - 1.0) / dt
            v -= x * x + x + x + 1.0
        out[i] = v
        p += dt
        if p >= 1.0:
            p -= 1.0
    return out


def pulse(n, freq, duty=0.5, phase=0.0):
    """Band-limited (PolyBLEP) pulse with DC removed. duty may be a list (PWM)."""
    fr = as_list(freq, n)
    du = as_list(duty, n)
    out = [0.0] * n
    p = phase % 1.0
    k = 1.0 / SR
    for i in range(n):
        dt = fr[i] * k
        d = du[i]
        v = (1.0 if p < d else -1.0) - (2.0 * d - 1.0)
        # rising edge at p = 0
        if p < dt:
            x = p / dt
            v += x + x - x * x - 1.0
        elif p > 1.0 - dt:
            x = (p - 1.0) / dt
            v += x * x + x + x + 1.0
        # falling edge at p = d
        q = p - d
        if q < 0.0:
            q += 1.0
        if q < dt:
            x = q / dt
            v -= x + x - x * x - 1.0
        elif q > 1.0 - dt:
            x = (q - 1.0) / dt
            v -= x * x + x + x + 1.0
        out[i] = v
        p += dt
        if p >= 1.0:
            p -= 1.0
    return out


def tri(n, freq, phase=0.25, steps=0):
    """Triangle. steps=16 gives the stepped 4-bit console triangle."""
    fr = as_list(freq, n)
    out = [0.0] * n
    p = phase % 1.0
    k = 1.0 / SR
    q = steps / 2.0 if steps else 0.0
    for i in range(n):
        v = 4.0 * abs(p - 0.5) - 1.0
        if q:
            v = int(v * q + q) / q - 1.0 + 0.5 / q
        out[i] = v
        p += fr[i] * k
        if p >= 1.0:
            p -= 1.0
    return out


def white(n, rng):
    r = rng.random
    return [2.0 * r() - 1.0 for _ in range(n)]


def chip_noise(n, rate, short=False, seed=1):
    """15-bit LFSR noise clocked at `rate` Hz (console noise channel).
    short=True is the metallic 93-step mode."""
    out = [0.0] * n
    reg = (seed * 2654435761) & 0x7FFF or 1
    tap = 6 if short else 1
    inc = rate / SR
    acc = 0.0
    v = 1.0
    for i in range(n):
        acc += inc
        while acc >= 1.0:
            acc -= 1.0
            bit = (reg ^ (reg >> tap)) & 1
            reg = (reg >> 1) | (bit << 14)
            v = 1.0 if reg & 1 else -1.0
        out[i] = v
    return out


def crackle(n, density, rng, decay=0.0015, lo=0.2, hi=1.0):
    """Sparse random decaying impulses (fire crackle, bone crunch, grit)."""
    out = [0.0] * n
    p = density / SR
    r = rng.random
    k = math.exp(-1.0 / (decay * SR))
    level = 0.0
    sign = 1.0
    for i in range(n):
        if r() < p:
            level = lo + (hi - lo) * r()
            sign = -sign
        out[i] = level * sign * (2.0 * r() - 1.0)
        level *= k
    return out


# ---------------------------------------------------------------- envelopes

def adsr(gate, a=0.005, d=0.1, s=0.7, r=0.1, curve_a=1.0):
    """Gate length in samples; a/d/r in seconds. Returns gate + release samples.
    Release ends at exactly zero."""
    na = max(1, ns(a))
    nr = max(1, ns(r))
    out = [0.0] * (gate + nr)
    kd = math.exp(-4.0 / max(1.0, d * SR))
    lvl = 0.0
    diff = 1.0 - s
    for i in range(gate):
        if i < na:
            x = (i + 1) / na
            lvl = x if curve_a == 1.0 else x ** curve_a
        else:
            diff *= kd
            lvl = s + diff
        out[i] = lvl
    e = math.exp
    for j in range(nr):
        x = j / nr
        out[gate + j] = lvl * e(-4.0 * x) * (1.0 - x)
    return out


def perc(n, a=0.001, t60=0.3, hold=0.0):
    """Attack then exponential decay reaching -60 dB at t60. Ends at zero."""
    na = max(1, ns(a))
    nh = ns(hold)
    out = [0.0] * n
    k = math.exp(-6.9078 / max(1.0, t60 * SR))
    lvl = 1.0
    tail = max(1, min(n // 8, ns(0.01)))
    for i in range(n):
        if i < na:
            v = (i + 1) / na
        elif i < na + nh:
            v = 1.0
        else:
            lvl *= k
            v = lvl
        if i >= n - tail:
            v *= (n - i) / tail
        out[i] = v
    return out


def swell(n, peak_at=0.5, power=2.0):
    """Smooth rise and fall over n samples (sin^p shape), peaking at peak_at."""
    out = [0.0] * n
    pk = max(1, int(n * peak_at))
    sin = math.sin
    for i in range(n):
        if i < pk:
            x = 0.5 * math.pi * i / pk
        else:
            x = 0.5 * math.pi * (1.0 + (i - pk) / max(1, n - pk))
        out[i] = abs(sin(x)) ** power
    return out


# ---------------------------------------------------------------- filters

def svf(x, cutoff, q=0.707, mode='lp', block=16):
    """Zavalishin TPT state-variable filter. cutoff may be a list (swept, updated
    every `block` samples). Modes: lp, bp (unity peak), hp, notch."""
    n = len(x)
    out = [0.0] * n
    k = 1.0 / q
    cl, cb, ch = {'lp': (1.0, 0.0, 0.0), 'bp': (0.0, k, 0.0),
                  'hp': (0.0, 0.0, 1.0), 'notch': (1.0, 0.0, 1.0)}[mode]
    swept = isinstance(cutoff, (list, array))
    tan = math.tan
    ny = SR * 0.45
    ic1 = ic2 = 0.0
    for b in range(0, n, block):
        fc = cutoff[b] if swept else cutoff
        fc = 10.0 if fc < 10.0 else (ny if fc > ny else fc)
        g = tan(math.pi * fc / SR)
        a1 = 1.0 / (1.0 + g * (g + k))
        a2 = g * a1
        a3 = g * a2
        for i in range(b, min(n, b + block)):
            v0 = x[i]
            v3 = v0 - ic2
            v1 = a1 * ic1 + a2 * v3
            v2 = ic2 + a2 * ic1 + a3 * v3
            ic1 = 2.0 * v1 - ic1
            ic2 = 2.0 * v2 - ic2
            out[i] = cl * v2 + cb * v1 + ch * (v0 - k * v1 - v2)
        if not swept:
            # constant cutoff: finish in one pass
            for i in range(b + block, n):
                v0 = x[i]
                v3 = v0 - ic2
                v1 = a1 * ic1 + a2 * v3
                v2 = ic2 + a2 * ic1 + a3 * v3
                ic1 = 2.0 * v1 - ic1
                ic2 = 2.0 * v2 - ic2
                out[i] = cl * v2 + cb * v1 + ch * (v0 - k * v1 - v2)
            break
    return out


def lp1(x, fc):
    """One-pole low-pass."""
    a = 1.0 - math.exp(-TAU * fc / SR)
    y = 0.0
    out = [0.0] * len(x)
    for i, v in enumerate(x):
        y += a * (v - y)
        out[i] = y
    return out


def hp1(x, fc):
    """One-pole high-pass."""
    a = 1.0 - math.exp(-TAU * fc / SR)
    y = 0.0
    out = [0.0] * len(x)
    for i, v in enumerate(x):
        y += a * (v - y)
        out[i] = v - y
    return out


def formants(x, bands, block=32):
    """Parallel resonators: bands = [(freq or list, q, gain), ...]."""
    out = [0.0] * len(x)
    for f, q, g in bands:
        y = svf(x, f, q, 'bp', block)
        for i, v in enumerate(y):
            out[i] += g * v
    return out


# ---------------------------------------------------------------- shaping and mixing

def drive(x, amount=2.0):
    """tanh soft clip, gain-compensated so small signals keep their level."""
    t = math.tanh
    k = 1.0 / amount
    return [t(amount * v) * k for v in x]


def mul(a, b):
    return [x * y for x, y in zip(a, b)]


def scale(a, g):
    return [x * g for x in a]


def mix(*parts):
    """mix((sig, gain), ...) -> list as long as the longest part."""
    n = max(len(s) for s, _ in parts)
    out = [0.0] * n
    for s, g in parts:
        for i, v in enumerate(s):
            out[i] += v * g
    return out


def pad_to(x, n):
    return list(x) + [0.0] * (n - len(x)) if len(x) < n else list(x[:n])


def delayed(x, seconds, total=None):
    d = ns(seconds)
    out = [0.0] * d + list(x)
    return pad_to(out, total) if total else out


def mix_into(dst, src, start, gain=1.0, wrap=False):
    """Add src*gain into dst at start. wrap=True wraps past the end (loops)."""
    n = len(dst)
    if wrap:
        start %= n
        i = start
        for v in src:
            dst[i] += v * gain
            i += 1
            if i == n:
                i = 0
        return
    for i in range(max(0, start), min(n, start + len(src))):
        dst[i] += src[i - start] * gain


def pan_gains(p):
    """Constant-power pan, p in [-1, 1]."""
    a = (p + 1.0) * math.pi / 4.0
    return math.cos(a) * math.sqrt(2.0), math.sin(a) * math.sqrt(2.0)


def fade_in(x, n):
    n = min(n, len(x))
    for i in range(n):
        x[i] *= 0.5 - 0.5 * math.cos(math.pi * i / n)
    return x


def fade_out(x, n):
    n = min(n, len(x))
    m = len(x)
    for i in range(n):
        x[m - 1 - i] *= 0.5 - 0.5 * math.cos(math.pi * i / n)
    return x


# ---------------------------------------------------------------- effects

def echo(x, seconds, feedback=0.35, wet=0.3, lp=3500.0, total=None):
    """Mono feedback delay with a low-passed loop. Returns dry + wet."""
    d = max(1, ns(seconds))
    n = total or len(x)
    a = 1.0 - math.exp(-TAU * lp / SR)
    line = [0.0] * d
    out = [0.0] * n
    z = 0.0
    j = 0
    m = len(x)
    for i in range(n):
        v = x[i] if i < m else 0.0
        y = line[j]
        z += a * (y - z)
        line[j] = v + z * feedback
        out[i] = v + wet * y
        j += 1
        if j == d:
            j = 0
    return out


def pingpong(src, seconds, feedback=0.4, lp=3500.0):
    """Stereo ping-pong delay fed by a mono send. Returns wet (left, right)."""
    d = max(1, ns(seconds))
    n = len(src)
    a = 1.0 - math.exp(-TAU * lp / SR)
    bl = [0.0] * d
    br = [0.0] * d
    ol = buf(n)
    orr = buf(n)
    z = 0.0
    j = 0
    for i in range(n):
        yl = bl[j]
        yr = br[j]
        z += a * (yr - z)
        bl[j] = src[i] + z * feedback
        br[j] = yl
        ol[i] = yl
        orr[i] = yr
        j += 1
        if j == d:
            j = 0
    return ol, orr


def reverb(src, rt60=1.8, size=1.0, damp=5500.0, predelay=0.015, src_r=None):
    """FDN reverb: predelay, two input diffusers, eight damped delay lines mixed by
    a Householder matrix, one output diffuser per side. Mono (or stereo) send in,
    wet (left, right) out."""
    n = len(src)
    pd_n = max(1, ns(predelay))
    pd = [0.0] * pd_n
    pj = 0
    lens = [max(8, int(v * size)) for v in (1031, 1153, 1279, 1381, 1493, 1609, 1733, 1867)]
    gains = [10.0 ** (-3.0 * L / (rt60 * SR)) for L in lens]
    lines = [[0.0] * L for L in lens]
    idx = [0] * 8
    zs = [0.0] * 8
    sign = (1.0, -1.0, 1.0, -1.0, 1.0, -1.0, 1.0, -1.0)
    a = 1.0 - math.exp(-TAU * damp / SR)
    ga = 0.62
    apl = [max(4, int(v * size)) for v in (149, 383, 241, 313)]
    ap0, ap1, apL, apR = [[0.0] * L for L in apl]
    m0, m1, mL, mR = apl
    j0 = j1 = jL = jR = 0
    ol = buf(n)
    orr = buf(n)
    rng8 = range(8)
    for i in range(n):
        x = src[i] if src_r is None else 0.5 * (src[i] + src_r[i])
        v = pd[pj]
        pd[pj] = x
        pj += 1
        if pj == pd_n:
            pj = 0
        b = ap0[j0]
        w = v + ga * b
        v = b - ga * w
        ap0[j0] = w
        j0 += 1
        if j0 == m0:
            j0 = 0
        b = ap1[j1]
        w = v + ga * b
        v = b - ga * w
        ap1[j1] = w
        j1 += 1
        if j1 == m1:
            j1 = 0
        s = 0.0
        for k in rng8:
            z = zs[k] + a * (lines[k][idx[k]] - zs[k])
            zs[k] = z
            s += z
        s *= 0.25
        for k in rng8:
            j = idx[k]
            lines[k][j] = (zs[k] - s) * gains[k] + sign[k] * v
            j += 1
            idx[k] = 0 if j == lens[k] else j
        xl = zs[0] - zs[2] + zs[4] - zs[6]
        xr = zs[1] - zs[3] + zs[5] - zs[7]
        b = apL[jL]
        w = xl + 0.5 * b
        ol[i] = 0.5 * (b - 0.5 * w)
        apL[jL] = w
        jL += 1
        if jL == mL:
            jL = 0
        b = apR[jR]
        w = xr + 0.5 * b
        orr[i] = 0.5 * (b - 0.5 * w)
        apR[jR] = w
        jR += 1
        if jR == mR:
            jR = 0
    return ol, orr


def loop_fx(fx, *signals, cycles=2):
    """Run a stateful effect over `cycles` repeats of a loop and keep the last
    cycle, so the effect's tail wraps into the start and the loop stays seamless."""
    L = len(signals[0])
    rep = [array('d', s) * cycles for s in signals]
    res = fx(*rep)
    if isinstance(res, tuple):
        return tuple(array('d', r[-L:]) for r in res)
    return array('d', res[-L:])


# ---------------------------------------------------------------- analysis

def peak(x):
    return max((abs(v) for v in x), default=0.0)


def rms(x):
    return math.sqrt(sum(v * v for v in x) / max(1, len(x)))


def db(v):
    return 20.0 * math.log10(v) if v > 0 else -200.0


def _biquad(x, b0, b1, b2, a1, a2):
    out = [0.0] * len(x)
    x1 = x2 = y1 = y2 = 0.0
    for i, v in enumerate(x):
        y = b0 * v + b1 * x1 + b2 * x2 - a1 * y1 - a2 * y2
        x2 = x1
        x1 = v
        y2 = y1
        y1 = y
        out[i] = y
    return out


def kweight(x, sr=SR):
    """ITU-R BS.1770 K-weighting (shelf + RLB high-pass) for any sample rate."""
    G, Q, fc = 3.999843853973347, 0.7071752369554196, 1681.974450955533
    A = 10.0 ** (G / 40.0)
    w0 = TAU * fc / sr
    al = math.sin(w0) / (2.0 * Q)
    c = math.cos(w0)
    sa = 2.0 * math.sqrt(A) * al
    a0 = (A + 1) - (A - 1) * c + sa
    y = _biquad(x, A * ((A + 1) + (A - 1) * c + sa) / a0, -2 * A * ((A - 1) + (A + 1) * c) / a0,
                A * ((A + 1) + (A - 1) * c - sa) / a0, 2 * ((A - 1) - (A + 1) * c) / a0,
                ((A + 1) - (A - 1) * c - sa) / a0)
    Q, fc = 0.5003270373238773, 38.13547087602444
    w0 = TAU * fc / sr
    al = math.sin(w0) / (2.0 * Q)
    c = math.cos(w0)
    a0 = 1 + al
    return _biquad(y, (1 + c) / 2 / a0, -(1 + c) / a0, (1 + c) / 2 / a0, -2 * c / a0, (1 - al) / a0)


def _block_powers(chans, sr=SR, win=0.4, hop=0.1):
    kw = [kweight(c, sr) for c in chans]
    n = len(kw[0])
    w = int(win * sr)
    h = int(hop * sr)
    # prefix sums of squared samples per channel
    pre = []
    for c in kw:
        p = [0.0] * (n + 1)
        s = 0.0
        for i, v in enumerate(c):
            s += v * v
            p[i + 1] = s
        pre.append(p)
    if n < w:
        return [sum(p[n] for p in pre) / max(1, w)]
    return [sum(p[i + w] - p[i] for p in pre) / w for i in range(0, n - w + 1, h)]


def _lufs(power):
    return -0.691 + 10.0 * math.log10(power) if power > 0 else -200.0


def loudness(chans, sr=SR):
    """Integrated loudness (LUFS) with the BS.1770 absolute and relative gates."""
    blocks = _block_powers(chans, sr)
    g1 = [p for p in blocks if _lufs(p) > -70.0]
    if not g1:
        return -200.0
    rel = _lufs(sum(g1) / len(g1)) - 10.0
    g2 = [p for p in g1 if _lufs(p) > rel]
    return _lufs(sum(g2) / len(g2))


def momentary_max(chans, sr=SR):
    """Loudest 400 ms window (LUFS). Good single number for short sounds."""
    return _lufs(max(_block_powers(chans, sr, hop=0.02)))
