"""Sequencer, notation and instruments for the music tracks.

Notation: a line is space-separated tokens `<note>/<steps>`, e.g. `A4/2 D5/2 F5/6`.
A step is a 16th note. `r/4` is a rest, a trailing `!` accents and `?` softens a
note, a bare note reuses the previous length, and `|` marks a bar line. In a barred
line every bar's length is checked, so a miscounted bar fails the build.
"""

import math
import random
from array import array

from dsp import (SR, TAU, adsr, buf, cents, chip_noise, curve, drive, formants, hz,
                 loop_fx, loudness, mix_into, note, ns, pan_gains, perc, pingpong, pulse,
                 reverb, saw, sine, svf, tri, vibrato, white, hp1)

# Set True (build_audio.py --levels) to keep each part's dry signal and report its
# loudness, which is how the mix was balanced without listening.
ANALYZE = False


# ---------------------------------------------------------------- song and buses

class Song:
    """A grid of 16th-note steps rendered into stereo dry, reverb and delay buses.
    Loops wrap note tails and effect tails around the end so they join seamlessly."""

    def __init__(self, bpm, bars, steps_per_bar=16, loop=True, tail=0.0, seed=1):
        self.spb = steps_per_bar
        self.bars = bars
        self.steps = bars * steps_per_bar
        self.step = int(round(SR * 60.0 / (bpm * 4)))
        self.loop = loop
        if loop:
            # Ogg Vorbis stores the length rounded up to 64 samples, so a loop is
            # only sample-exact when its length is a multiple of 64.
            while (self.steps * self.step) % 64:
                self.step += 1
        self.bpm = SR * 60.0 / (self.step * 4)
        self.n = self.steps * self.step
        self.size = self.n if loop else self.n + ns(tail)
        self.dry_l = buf(self.size)
        self.dry_r = buf(self.size)
        self.rev = buf(self.size)
        self.dly = buf(self.size)
        self.rng = random.Random(seed)
        self.parts = {}

    def at(self, step):
        return int(round(step * self.step))

    def put(self, step, sig, gain=1.0, pan=0.0, rev=0.0, dly=0.0, name='', sig_r=None):
        start = self.at(step)
        w = self.loop
        if sig_r is None:
            gl, gr = pan_gains(pan)
            mix_into(self.dry_l, sig, start, gain * gl, w)
            mix_into(self.dry_r, sig, start, gain * gr, w)
            if rev:
                mix_into(self.rev, sig, start, gain * rev, w)
            if dly:
                mix_into(self.dly, sig, start, gain * dly, w)
        else:
            mix_into(self.dry_l, sig, start, gain, w)
            mix_into(self.dry_r, sig_r, start, gain, w)
            if rev:
                mix_into(self.rev, sig, start, 0.5 * gain * rev, w)
                mix_into(self.rev, sig_r, start, 0.5 * gain * rev, w)
            if dly:
                mix_into(self.dly, sig, start, 0.5 * gain * dly, w)
                mix_into(self.dly, sig_r, start, 0.5 * gain * dly, w)
        if ANALYZE and name:
            part = self.parts.setdefault(name, buf(self.size))
            mix_into(part, sig, start, gain, w)
            if sig_r is not None:
                mix_into(part, sig_r, start, gain, w)

    def levels(self):
        """Loudness (LUFS, active passages only) of each part's dry signal."""
        return {k: round(loudness([v]), 1) for k, v in sorted(self.parts.items())}

    def mixdown(self, rt60=2.0, size=1.0, damp=5000.0, rev_gain=1.0, predelay=0.02,
                dly_steps=3, dly_fb=0.35, dly_lp=3200.0, dly_gain=1.0, hp=28.0):
        """Run the delay and reverb sends (wrapped for loops) and sum to stereo."""
        dt = dly_steps * self.step / SR
        if self.loop:
            wl, wr = loop_fx(lambda s: pingpong(s, dt, dly_fb, dly_lp), self.dly)
        else:
            wl, wr = pingpong(self.dly, dt, dly_fb, dly_lp)
        rev = self.rev
        for i in range(self.size):
            rev[i] += 0.3 * (wl[i] + wr[i])
        fx = lambda s: reverb(s, rt60, size, damp, predelay)
        rl, rr = loop_fx(fx, rev) if self.loop else fx(rev)
        L = array('d', (a + dly_gain * b + rev_gain * c for a, b, c in zip(self.dry_l, wl, rl)))
        R = array('d', (a + dly_gain * b + rev_gain * c for a, b, c in zip(self.dry_r, wr, rr)))
        if hp:
            if self.loop:
                L = loop_fx(lambda s: hp1(s, hp), L)
                R = loop_fx(lambda s: hp1(s, hp), R)
            else:
                L, R = hp1(L, hp), hp1(R, hp)
        return L, R


# ---------------------------------------------------------------- notation

def parse_line(text, spb=16):
    """-> [(start_step, length_steps, midi, accent)], total_steps"""
    events = []
    pos = bar0 = 0.0
    length = 4.0
    for tok in text.split():
        if tok == '|':
            if abs(pos - bar0 - spb) > 1e-9:
                raise ValueError(f'bar starting at step {bar0:g} has {pos - bar0:g} steps in: {text}')
            bar0 = pos
            continue
        name, _, ln = tok.partition('/')
        if ln:
            length = float(ln)
        acc = 1.0
        if name.endswith('!'):
            name, acc = name[:-1], 1.25
        elif name.endswith('?'):
            name, acc = name[:-1], 0.7
        if name != 'r':
            events.append((pos, length, note(name), acc))
        pos += length
    if '|' in text and pos != bar0:
        raise ValueError(f'unfinished bar ({pos - bar0:g} steps) at the end of: {text}')
    return events, pos


QUALITIES = {
    '': (0, 4, 7), 'm': (0, 3, 7), 'dim': (0, 3, 6), 'aug': (0, 4, 8), '5': (0, 7),
    'sus2': (0, 2, 7), 'sus4': (0, 5, 7), '7': (0, 4, 7, 10), 'm7': (0, 3, 7, 10),
    'maj7': (0, 4, 7, 11), 'm6': (0, 3, 7, 9), 'add9': (0, 4, 7, 14), 'madd9': (0, 3, 7, 14),
    'm9': (0, 3, 7, 10, 14), '7sus4': (0, 5, 7, 10), 'm7b5': (0, 3, 6, 10),
}


def parse_chord(sym):
    i = 1
    while i < len(sym) and sym[i] in '#b':
        i += 1
    root = note(sym[:i] + '0') % 12
    return root, QUALITIES[sym[i:]]


class Chords:
    """Chord timeline from 'Dm | Bb | C Am | ...' (two chords in a bar split it)."""

    def __init__(self, text, spb=16):
        self.items = []
        pos = 0
        for bar in text.split('|'):
            syms = bar.split()
            if not syms:
                continue
            ln = spb / len(syms)
            for s in syms:
                root, ivs = parse_chord(s)
                self.items.append((pos, ln, root, ivs, s))
                pos += ln
        self.total = pos

    def at(self, step):
        step %= self.total
        for it in self.items:
            if it[0] <= step < it[0] + it[1]:
                return it
        return self.items[-1]

    def spans(self, bar0=0, bar1=None, spb=16):
        """Chord items in [bar0, bar1), with repeats of the same chord merged."""
        lo, hi = bar0 * spb, (bar1 * spb if bar1 is not None else self.total)
        out = []
        for pos, ln, root, ivs, sym in self.items:
            if lo <= pos < hi:
                if out and out[-1][4] == sym and out[-1][0] + out[-1][1] == pos:
                    p, l, r, iv, s = out[-1]
                    out[-1] = (p, l + ln, r, iv, s)
                else:
                    out.append((pos, ln, root, ivs, sym))
        return out


def voicing(root, ivs, prev, lo, hi):
    """Closest close-position voicing to the previous chord, inside [lo, hi]."""
    pcs = []
    for iv in ivs:
        pc = (root + iv) % 12
        if pc not in pcs:
            pcs.append(pc)
    cands = []
    for r in range(len(pcs)):
        order = pcs[r:] + pcs[:r]
        v = [lo + (order[0] - lo) % 12]
        for pc in order[1:]:
            v.append(v[-1] + ((pc - v[-1]) % 12 or 12))
        if v[-1] <= hi:
            cands.append(v)
    if not cands:
        for r in range(len(pcs)):
            order = pcs[r:] + pcs[:r]
            v = [lo + (order[0] - lo) % 12]
            for pc in order[1:]:
                v.append(v[-1] + ((pc - v[-1]) % 12 or 12))
            cands.append(v)
    mid = (lo + hi) / 2
    if prev is None:
        return min(cands, key=lambda v: abs(sum(v) / len(v) - mid))
    return min(cands, key=lambda v: sum(min(abs(a - b) for b in prev) for a in v)
               + 0.2 * abs(sum(v) / len(v) - mid))


DEGREES = {'R': 0, 'O': 12, 'b2': 1, '2': 2, '4': 5, 'b5': 6, '6': 9, 'b7': 10,
           '-R': -12, '-5': -5, '-b7': -2, 'O5': 19}


def degree(tok, ivs):
    if tok == '3':
        return next((i for i in ivs if i in (3, 4)), 4)
    if tok == '5':
        return next((i for i in ivs if i in (6, 7, 8)), 7)
    if tok == '7':
        return next((i for i in ivs if i in (10, 11)), 10)
    return DEGREES[tok]


# ---------------------------------------------------------------- voices

class Voice:
    """An instrument with mix settings, playing lines or chord-derived patterns."""

    def __init__(self, song, inst, name, gain=0.3, pan=0.0, rev=0.2, dly=0.0, gate=0.95, **params):
        self.s = song
        self.inst = inst
        self.name = name
        self.gain = gain
        self.pan = pan
        self.rev = rev
        self.dly = dly
        self.gate = gate
        self.params = params

    def play(self, step, length, midi, vel=1.0):
        gate_n = max(64, int(length * self.s.step * self.gate))
        sig = self.inst(midi, gate_n, vel, self.s.rng, **self.params)
        if isinstance(sig, tuple):
            self.s.put(step, sig[0], self.gain, 0.0, self.rev, self.dly, self.name, sig_r=sig[1])
        else:
            self.s.put(step, sig, self.gain, self.pan, self.rev, self.dly, self.name)

    def line(self, bar, text, transpose=0, vel=1.0):
        events, _ = parse_line(text, self.s.spb)
        for pos, ln, midi, acc in events:
            self.play(bar * self.s.spb + pos, ln, midi + transpose, vel * acc)

    def bass(self, chords, bar0, bar1, pattern, lo=36, vel=1.0):
        """Repeat a one-bar degree pattern ('R/4 5/2 O/2 ...') over each bar."""
        toks = []
        length = 4.0
        for t in pattern.split():
            d, _, ln = t.partition('/')
            if ln:
                length = float(ln)
            toks.append((d, length))
        for bar in range(bar0, bar1):
            pos = bar * self.s.spb
            for d, ln in toks:
                if d != 'r':
                    acc = 1.0
                    if d.endswith('!'):
                        d, acc = d[:-1], 1.2
                    _, _, root, ivs, _ = chords.at(pos)
                    base = lo + (root - lo) % 12
                    self.play(pos, ln, base + degree(d, ivs), vel * acc)
                pos += ln

    def chords(self, chords, bar0, bar1, lo=50, hi=70, vel=1.0):
        """Sustained chords (merged across repeated bars) - for pads."""
        prev = None
        for pos, ln, root, ivs, _ in chords.spans(bar0, bar1, self.s.spb):
            v = voicing(root, ivs, prev, lo, hi)
            prev = v
            self.play(pos, ln, v, vel)

    def stabs(self, chords, bar0, bar1, rhythm, length=1.0, lo=57, hi=74, vel=1.0):
        """Short chord hits on the x/X positions of a one-bar rhythm string."""
        prev = None
        for bar in range(bar0, bar1):
            for k, c in enumerate(rhythm):
                if c in 'xX':
                    pos = bar * self.s.spb + k
                    _, _, root, ivs, _ = chords.at(pos)
                    prev = voicing(root, ivs, prev, lo, hi)
                    self.play(pos, length, prev, vel * (1.2 if c == 'X' else 1.0))

    def arp(self, chords, bar0, bar1, order, rate=1.0, lo=62, hi=86, vel=1.0):
        """Arpeggiate chord tones (voiced from lo upward) in `order` index steps."""
        pos = bar0 * self.s.spb
        k = 0
        while pos < bar1 * self.s.spb:
            _, _, root, ivs, _ = chords.at(pos)
            tones = voicing(root, ivs, None, lo, hi)
            ext = tones + [t + 12 for t in tones]
            self.play(pos, rate, ext[order[k % len(order)] % len(ext)], vel)
            pos += rate
            k += 1


# ---------------------------------------------------------------- instruments
# Each takes (midi, gate_samples, velocity, rng, **params) and returns a mono list
# (or a (left, right) pair). Pads take a list of MIDI notes.

def lead(midi, gate, vel, rng, duty=0.25, a=0.006, d=0.3, s=0.62, r=0.12, vib=11.0,
         rate=5.4, bright=4200.0, pwm=0.05, scoop=-30.0):
    """Pulse lead: delayed vibrato, a small pitch scoop on the attack, slow PWM."""
    f = hz(midi)
    n = gate + ns(r)
    fr = vibrato(n, f, rate, vib, delay=0.16, ramp=0.3, phase=rng.random() * TAU)
    ks = ns(0.035)
    for i in range(min(n, ks)):
        fr[i] *= cents(scoop * (1.0 - i / ks) ** 2)
    if pwm:
        ph = rng.random() * TAU
        w = TAU * 0.7 / SR
        du = [duty + pwm * math.sin(ph + w * i) for i in range(n)]
    else:
        du = duty
    x = svf(pulse(n, fr, du), bright, 0.6)
    env = adsr(gate, a, d, s, r)
    return [v * e * vel for v, e in zip(x, env)]


def brass(midi, gate, vel, rng, a=0.05, d=0.4, s=0.7, r=0.18, cut=900.0, peak=3200.0,
          q=1.1, vib=14.0, detune=7.0):
    """Two detuned saws through a swelling low-pass: a dark synth brass."""
    f = hz(midi)
    n = gate + ns(r)
    ph = rng.random() * TAU
    f1 = vibrato(n, f * cents(-detune), 5.0, vib, 0.2, 0.35, ph)
    f2 = vibrato(n, f * cents(detune), 5.0, vib, 0.2, 0.35, ph + 0.5)
    x = [p + q2 for p, q2 in zip(saw(n, f1, rng.random()), saw(n, f2, rng.random()))]
    co = curve(n, [(0, cut), (a + 0.03, peak), (a + 0.4, cut * 1.6)], exp=True)
    y = drive(svf(x, co, q), 1.6)
    env = adsr(gate, a, d, s, r, curve_a=1.5)
    return [v * e * vel * 0.9 for v, e in zip(y, env)]


def tri_bass(midi, gate, vel, rng, steps=16, a=0.003, d=0.35, s=0.8, r=0.05, sub=0.3):
    """Console-style stepped triangle bass with a little sine for weight."""
    f = hz(midi)
    n = gate + ns(r)
    x = tri(n, f, steps=steps)
    sb = sine(n, f)
    env = adsr(gate, a, d, s, r)
    y = svf([u + sub * w for u, w in zip(x, sb)], 2600.0, 0.6)
    return [v * e * vel for v, e in zip(y, env)]


def saw_bass(midi, gate, vel, rng, cut=260.0, env_amt=1600.0, env_t=0.07, q=1.3, amt=2.2,
             sub=0.45, detune=6.0, a=0.002, d=0.25, s=0.85, r=0.05):
    """Detuned saws with a plucked filter envelope, a sine underneath, then drive."""
    f = hz(midi)
    n = gate + ns(r)
    x1 = saw(n, f * cents(-detune), rng.random())
    x2 = saw(n, f * cents(detune), rng.random())
    k = math.exp(-1.0 / (env_t * SR))
    co = [0.0] * n
    e = env_amt
    for i in range(n):
        co[i] = cut + e
        e *= k
    y = svf([0.5 * (u + w) for u, w in zip(x1, x2)], co, q)
    sb = sine(n, f)
    y = drive([u + sub * w for u, w in zip(y, sb)], amt)
    env = adsr(gate, a, d, s, r)
    return [v * e2 * vel for v, e2 in zip(y, env)]


def pad(midis, gate, vel, rng, cutoff=1300.0, q=0.75, a=0.6, d=1.0, s=0.85, r=1.2,
        detune=8.0, lfo=0.13, depth=0.3, shape='saw'):
    """Stereo detuned saw (or pulse) chord through a slowly breathing low-pass."""
    if isinstance(midis, int):
        midis = [midis]
    n = gate + ns(r)
    L = [0.0] * n
    R = [0.0] * n
    osc = saw if shape == 'saw' else (lambda m, f, p: pulse(m, f, 0.35, p))
    for m in midis:
        f = hz(m)
        for side, sgn in ((L, 1.0), (R, -1.0)):
            for dc in (detune * sgn, -detune * 0.35 * sgn):
                x = osc(n, f * cents(dc), rng.random())
                for i, v in enumerate(x):
                    side[i] += v
    ph = rng.random() * TAU
    w = TAU * lfo / SR
    co = [cutoff * (1.0 + depth * math.sin(ph + w * i)) for i in range(0, n)]
    L = svf(L, co, q, block=64)
    R = svf(R, co, q, block=64)
    env = adsr(gate, a, d, s, r, curve_a=2.0)
    g = vel / (2.0 * len(midis)) ** 0.5
    return [v * e * g for v, e in zip(L, env)], [v * e * g for v, e in zip(R, env)]


def choir(midis, gate, vel, rng, a=0.9, r=1.6, vowel='ah', detune=10.0):
    """Saw stack through vowel formants: a wordless, ominous choir pad."""
    F = {'ah': ((730, 9, 1.0), (1090, 10, 0.55), (2440, 12, 0.25)),
         'oo': ((300, 8, 1.0), (870, 10, 0.35), (2240, 12, 0.12)),
         'oh': ((570, 9, 1.0), (840, 10, 0.5), (2410, 12, 0.18))}[vowel]
    if isinstance(midis, int):
        midis = [midis]
    n = gate + ns(r)
    L = [0.0] * n
    R = [0.0] * n
    for m in midis:
        f = hz(m)
        for side, sgn in ((L, 1.0), (R, -1.0)):
            for dc in (detune * sgn, -detune * 0.5 * sgn, 0.0):
                fr = vibrato(n, f * cents(dc), 4.6 + rng.random(), 9.0, 0.0, 1.0, rng.random() * TAU)
                for i, v in enumerate(saw(n, fr, rng.random())):
                    side[i] += v
    L = formants(L, F)
    R = formants(R, F)
    env = adsr(gate, a, 1.0, 0.9, r, curve_a=2.0)
    g = 1.6 * vel / (3.0 * len(midis)) ** 0.5
    return [v * e * g for v, e in zip(L, env)], [v * e * g for v, e in zip(R, env)]


def pluck(midi, gate, vel, rng, duty=0.125, t60=0.35, bright=5200.0):
    """Short pulse pluck for arpeggios."""
    f = hz(midi)
    n = max(gate, ns(t60))
    x = svf(pulse(n, f, duty, rng.random()), bright, 0.7)
    env = perc(n, 0.002, t60)
    return [v * e * vel for v, e in zip(x, env)]


def bell(midi, gate, vel, rng, kind='glass', t60=2.4):
    """'glass': FM chime for melodies. 'church': additive bell with hum, tierce
    (minor third) and beating partial pairs, for tolls."""
    f = hz(midi)
    if kind == 'glass':
        n = ns(t60)
        ix = curve(n, [(0, 2.2), (0.25, 0.6), (t60, 0.2)], exp=True)
        w1 = TAU * f / SR
        w2 = TAU * f * 3.5 / SR
        sin = math.sin
        x = [sin(w1 * i + ix[i] * sin(w2 * i)) for i in range(n)]
        sh = sine(n, f * 2.0)
        env = perc(n, 0.002, t60)
        env2 = perc(n, 0.001, t60 * 0.35)
        return [(v * e + 0.25 * u * e2) * vel for v, u, e, e2 in zip(x, sh, env, env2)]
    n = ns(t60)
    parts = ((0.5, 0.5, 1.0), (1.0, 0.8, 0.7), (1.003, 0.4, 0.7), (1.19, 0.55, 0.55),
             (1.5, 0.3, 0.45), (2.0, 0.45, 0.35), (2.006, 0.2, 0.35), (2.74, 0.22, 0.22),
             (3.76, 0.15, 0.15), (5.4, 0.08, 0.1))
    out = [0.0] * n
    for ratio, amp, dec in parts:
        x = sine(n, f * ratio, rng.random() * TAU)
        env = perc(n, 0.003, t60 * dec)
        for i in range(n):
            out[i] += x[i] * env[i] * amp
    return [v * vel * 0.45 for v in out]


def soft_tri(midi, gate, vel, rng, a=0.02, d=0.5, s=0.7, r=0.4, vib=6.0):
    """Smooth triangle, flute-like: for counter-lines in quiet tracks."""
    f = hz(midi)
    n = gate + ns(r)
    fr = vibrato(n, f, 4.8, vib, 0.25, 0.5, rng.random() * TAU)
    x = tri(n, fr)
    env = adsr(gate, a, d, s, r, curve_a=1.5)
    return [v * e * vel for v, e in zip(x, env)]


def poly(inst):
    """Let a mono instrument take a list of notes (for chord stabs)."""
    def play(midis, gate, vel, rng, **kw):
        sigs = [inst(m, gate, vel, rng, **kw) for m in midis]
        n = max(len(s) for s in sigs)
        g = 1.0 / len(sigs) ** 0.5
        out = [0.0] * n
        for s in sigs:
            for i, v in enumerate(s):
                out[i] += v * g
        return out
    return play


# ---------------------------------------------------------------- drums (noise based)

class Kit:
    """One-shot drums rendered once per song, then mixed at pattern positions."""

    HAT_FREQS = (205.3, 304.4, 369.6, 522.7, 540.0, 800.0)

    def __init__(self, song, seed=7, kick=None, snare=None, gain=1.0, rev=0.12, levels=None):
        self.s = song
        self.rng = random.Random(seed)
        self.gain = gain
        self.rev = rev
        kick = kick or {}
        snare = snare or {}
        self.sounds = {
            'k': [self._kick(**kick)],
            's': [self._snare(**snare) for _ in range(2)],
            'h': [self._hat(0.045) for _ in range(3)],
            'H': [self._hat(0.32)],
            'c': [self._crash()],
            't': [self._tom(165.0)],
            'T': [self._tom(98.0)],
            'B': [self._tom(52.0, t60=1.1, noise=0.15)],
            'r': [self._rim()],
        }
        for vs in self.sounds.values():
            for sig in vs:
                top = max(abs(v) for v in sig)
                for i in range(len(sig)):
                    sig[i] /= top
        # (gain, pan, reverb send) per drum, balanced by measured loudness
        self.mix = {'k': (0.62, 0.0, 0.05), 's': (0.75, 0.05, 0.22), 'h': (0.22, 0.35, 0.05),
                    'H': (0.16, 0.35, 0.1), 'c': (0.2, -0.3, 0.25), 't': (0.4, -0.25, 0.2),
                    'T': (0.45, 0.25, 0.2), 'B': (0.6, 0.0, 0.3), 'r': (0.5, -0.15, 0.15)}
        for key, g in (levels or {}).items():
            self.mix[key] = (g,) + self.mix[key][1:]
        self.count = 0

    def _kick(self, hi=150.0, lo=46.0, t60=0.42, click=0.3, amt=1.8):
        n = ns(t60)
        fr = curve(n, [(0, hi), (0.012, hi * 0.8), (0.06, lo * 1.15), (t60, lo)], exp=True)
        body = sine(n, fr)
        env = perc(n, 0.0012, t60)
        ck = svf(white(ns(0.012), self.rng), 2500.0, 0.8, 'hp')
        cke = perc(len(ck), 0.0003, 0.012)
        y = [b * e for b, e in zip(body, env)]
        for i in range(len(ck)):
            y[i] += click * ck[i] * cke[i]
        return drive(y, amt)

    def _snare(self, tone=190.0, t_tone=0.11, t_noise=0.2, chip=0.35):
        n = ns(max(t_tone, t_noise) + 0.02)
        fr = curve(n, [(0, tone * 1.5), (0.015, tone)], exp=True)
        body = tri(n, fr)
        nz = white(n, self.rng)
        ch = chip_noise(n, 18000.0, seed=self.rng.randint(1, 999))
        nz = svf([a + chip * b for a, b in zip(nz, ch)], 1400.0, 0.7, 'hp')
        nz = svf(nz, 7500.0, 0.7)
        e1 = perc(n, 0.001, t_tone)
        e2 = perc(n, 0.001, t_noise)
        return drive([0.7 * b * a + 0.75 * c * d for b, a, c, d in zip(body, e1, nz, e2)], 1.4)

    def _hat(self, t60):
        n = ns(t60 + 0.01)
        m = [0.0] * n
        for f in self.HAT_FREQS:
            for i, v in enumerate(pulse(n, f * 1.7, 0.5, self.rng.random())):
                m[i] += v
        nz = white(n, self.rng)
        x = svf([a / 6.0 + 0.6 * b for a, b in zip(m, nz)], 9000.0, 1.2, 'bp')
        x = svf(x, 6500.0, 0.7, 'hp')
        env = perc(n, 0.0008, t60)
        return [v * e * 1.6 for v, e in zip(x, env)]

    def _crash(self, t60=1.9):
        n = ns(t60)
        m = [0.0] * n
        for f in self.HAT_FREQS:
            for i, v in enumerate(pulse(n, f * 2.3, 0.5, self.rng.random())):
                m[i] += v
        nz = white(n, self.rng)
        x = svf([a / 6.0 * 0.5 + b for a, b in zip(m, nz)], 3800.0, 0.7, 'hp')
        x = svf(x, 11000.0, 0.7)
        env = perc(n, 0.002, t60)
        return [v * e for v, e in zip(x, env)]

    def _tom(self, f, t60=0.45, noise=0.25):
        n = ns(t60)
        fr = curve(n, [(0, f * 1.6), (0.05, f * 1.05), (t60, f * 0.9)], exp=True)
        body = sine(n, fr)
        nz = svf(white(n, self.rng), 1800.0, 0.7)
        e1 = perc(n, 0.0015, t60)
        e2 = perc(n, 0.001, 0.06)
        return drive([b * a + noise * c * d for b, a, c, d in zip(body, e1, nz, e2)], 1.5)

    def _rim(self):
        n = ns(0.06)
        t = tri(n, 830.0)
        nz = svf(white(n, self.rng), 2200.0, 1.5, 'bp')
        e = perc(n, 0.0005, 0.035)
        return [(0.6 * a + 0.8 * b) * c for a, b, c in zip(t, nz, e)]

    def bar(self, bar, rows, vel=1.0):
        """rows: {'k': 'x...x...', 's': '....x...', ...}; X accent, x normal, o ghost."""
        for key, pat in rows.items():
            gain, pan, rev = self.mix[key]
            for k, c in enumerate(pat):
                if c == '.':
                    continue
                v = {'X': 1.0, 'x': 0.78, 'o': 0.42}[c]
                if key in 'hs':
                    v *= 0.94 + 0.12 * self.rng.random()
                vs = self.sounds[key]
                sig = vs[self.count % len(vs)]
                self.count += 1
                self.s.put(bar * self.s.spb + k, sig, gain * v * vel * self.gain, pan, rev * self.rev / 0.12,
                           0.0, 'drum_' + key)
