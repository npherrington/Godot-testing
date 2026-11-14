"""Sound effects, all designed from scratch. One-shots return a mono list; the two
environment loops return a (left, right) pair whose length is an exact multiple of
64 samples. build_audio.py does fades, normalisation and encoding."""

import math
import random

from dsp import (SR, TAU, crackle, curve, drive, echo, formants, loop_fx, mix_into, mul,
                 ns, pan_gains, perc, pulse, reverb, saw, sine, smooth_random, svf, swell,
                 tri, white, zeros, hz, note, buf, lp1)


# ---------------------------------------------------------------- helpers

def place(out, sig, t, gain=1.0):
    mix_into(out, sig, ns(t), gain)
    return out


def room(x, rt60=0.5, wet=0.15, size=0.6, damp=6000.0, predelay=0.006):
    """Add a mono-summed reverb tail (the length grows by about rt60)."""
    src = list(x) + [0.0] * ns(rt60)
    l, r = reverb(src, rt60, size, damp, predelay)
    return [d + wet * (a + b) for d, a, b in zip(src, l, r)]


def env_mul(x, env):
    return [a * b for a, b in zip(x, env)]


def whoosh(rng, dur, f0, f1, f2, q=1.8, peak_at=0.45, power=2.0, sheen=0.35):
    """Band-passed noise sweeping f0 -> f1 -> f2 under a rise-and-fall envelope."""
    n = ns(dur)
    fc = curve(n, [(0, f0), (dur * peak_at, f1), (dur, f2)], exp=True)
    nz = white(n, rng)
    a = svf(nz, fc, q, 'bp')
    b = svf(nz, [f * 2.2 for f in fc], q * 1.6, 'bp')
    env = swell(n, peak_at, power)
    return [(x + sheen * y) * e for x, y, e in zip(a, b, env)]


def thump(f_hi, f_lo, t60, drop=0.03):
    n = ns(t60)
    fr = curve(n, [(0, f_hi), (drop, f_lo * 1.2), (t60, f_lo)], exp=True)
    return env_mul(sine(n, fr), perc(n, 0.0008, t60))


def noise_hit(rng, dur, fc, q, mode='bp', t60=None, a=0.0004):
    n = ns(dur)
    return env_mul(svf(white(n, rng), fc, q, mode), perc(n, a, t60 or dur))


def metal(rng, dur, f, ratios, t60, detune=0.004, amps=None):
    """Inharmonic struck-metal partials, higher ones dying faster."""
    n = ns(dur)
    out = zeros(n)
    for k, r in enumerate(ratios):
        fr = f * r * (1.0 + rng.uniform(-detune, detune))
        x = sine(n, fr, rng.random() * TAU)
        e = perc(n, 0.0008, t60 * (1.0 - 0.55 * k / len(ratios)))
        g = amps[k] if amps else 1.0 / (1.0 + 0.6 * k)
        for i in range(n):
            out[i] += x[i] * e[i] * g
    return out


def creature(rng, dur, pitch, f1, f2, f3, rough=0.4, breath=0.25, jitter=0.03, flutter=0.0,
             flut_rate=28.0, amt=2.5, vib=0.0, vib_rate=6.0, q=(5.0, 7.0, 9.0),
             gains=(1.0, 0.6, 0.25), env=None):
    """Formant-filtered buzz: saw source with pitch jitter, sub-harmonic roughness
    (growl), random flutter and breath noise, through three moving formants."""
    n = ns(dur)
    f0 = curve(n, pitch, exp=True)
    jit = smooth_random(n, 22.0, rng)
    fr = [f * (1.0 + jitter * j) for f, j in zip(f0, jit)]
    if vib:
        w = TAU * vib_rate / SR
        fr = [f * (1.0 + vib * math.sin(w * i)) for i, f in enumerate(fr)]
    src = saw(n, fr)
    if rough:
        sub = sine(n, [f * 0.5 for f in fr])
        rc = rough if isinstance(rough, (int, float)) else None
        rl = None if rc is not None else curve(n, rough)
        src = [s * (1.0 - (rc if rl is None else rl[i]) * 0.5 * (1.0 + u))
               for i, (s, u) in enumerate(zip(src, sub))]
    if flutter:
        fl = smooth_random(n, flut_rate, rng, 0.0, 1.0)
        src = [s * (1.0 - flutter * f) for s, f in zip(src, fl)]
    nz = white(n, rng)
    exc = [s + breath * z for s, z in zip(src, nz)]

    def c(v):
        return curve(n, v, exp=True) if isinstance(v, list) else v
    y = formants(exc, [(c(f1), q[0], gains[0]), (c(f2), q[1], gains[1]), (c(f3), q[2], gains[2])])
    y = drive(y, amt)
    e = env if env is not None else swell(n, 0.25, 1.2)
    return env_mul(y, e)


def env_ahr(n, a, hold, r):
    """Attack - hold - release envelope (release shaped to land on zero)."""
    na, nh = ns(a), ns(hold)
    out = [0.0] * n
    for i in range(n):
        if i < na:
            out[i] = (i + 1) / max(1, na)
        elif i < na + nh:
            out[i] = 1.0
        else:
            x = (i - na - nh) / max(1, n - na - nh)
            out[i] = math.exp(-3.0 * x) * (1.0 - x)
    return out


# ---------------------------------------------------------------- character actions

def footstep(v):
    """Boot on stone: heel knock (low thump + hard click), dusty scrape, toe tap,
    small stone-room reflection. Four variants differ in pitch, timing and grit."""
    rng = random.Random(1000 + v)
    out = zeros(ns(0.2))
    f0 = (92.0, 104.0, 86.0, 98.0)[v - 1] * rng.uniform(0.97, 1.03)
    place(out, thump(f0 * 1.9, f0 * 0.7, 0.07, 0.012), 0.0, 0.9)
    place(out, noise_hit(rng, 0.03, (2400.0, 2900.0, 2100.0, 2600.0)[v - 1], 0.9, t60=0.02), 0.0, 0.75)
    gn = ns(0.06)
    grit = svf(crackle(gn, 2600.0, rng, decay=0.0005), 4200.0, 0.8, 'bp')
    place(out, env_mul(grit, swell(gn, 0.2, 1.0)), 0.004, 0.35)
    toe = (0.048, 0.057, 0.043, 0.052)[v - 1]
    place(out, noise_hit(rng, 0.03, (1700.0, 1500.0, 1900.0, 1600.0)[v - 1], 1.1, t60=0.022), toe, 0.45)
    place(out, thump(f0 * 2.4, f0 * 1.1, 0.035, 0.008), toe, 0.3)
    return room(out, rt60=0.4, wet=0.22, size=0.45, damp=5000.0)


def player_attack(v):
    """The player's sword slash: a fast whoosh, then the blade's metallic ring."""
    rng = random.Random(2000 + v)
    if v == 1:
        w = whoosh(rng, 0.26, 500.0, 2600.0, 700.0, q=2.0, peak_at=0.4)
        ring = metal(rng, 0.45, 2350.0, (1.0, 1.47, 2.09, 2.56, 3.21), 0.35)
        t = 0.05
    else:
        w = whoosh(rng, 0.32, 380.0, 2000.0, 520.0, q=1.8, peak_at=0.5)
        ring = metal(rng, 0.5, 1980.0, (1.0, 1.52, 2.13, 2.71, 3.33), 0.4)
        t = 0.08
    out = zeros(ns(0.62))
    place(out, w, 0.0, 1.0)
    scrape = env_mul(svf(white(ns(0.09), rng), curve(ns(0.09), [(0, 7000.0), (0.09, 3500.0)], exp=True),
                         2.5, 'bp'), swell(ns(0.09), 0.3, 1.5))
    place(out, scrape, t - 0.02, 0.35)
    place(out, env_mul(ring, swell(len(ring), 0.03, 0.6)), t, 0.16)
    return room(out, rt60=0.6, wet=0.12, size=0.6)


def pickup(v):
    """Item pickup. 1: quick three-note blip for common items.
    2: five-note major arpeggio with shimmer, for rarer finds."""
    rng = random.Random(3000 + v)
    if v == 1:
        notes, dt, last = ('A5', 'D6', 'A6'), 0.045, 0.22
    else:
        notes, dt, last = ('D6', 'F#6', 'A6', 'D7', 'F#7'), 0.05, 0.4
    out = zeros(ns(dt * len(notes) + last + 0.05))
    for k, nm in enumerate(notes):
        f = hz(note(nm))
        length = last if k == len(notes) - 1 else dt * 1.6
        n = ns(length)
        x = svf(pulse(n, f, 0.25), 6000.0, 0.7)
        x2 = tri(n, f * 0.5)
        e = perc(n, 0.002, length)
        sig = [(a + 0.5 * b) * c for a, b, c in zip(x, x2, e)]
        place(out, sig, k * dt, 0.8 if k < len(notes) - 1 else 1.0)
    sn = ns(last)
    sp = mul(sine(sn, hz(note(notes[-1])) * 2.0), perc(sn, 0.001, last * 0.6))
    place(out, sp, dt * (len(notes) - 1), 0.25)
    if v == 2:
        for k in range(6):
            gn = ns(0.12)
            g = mul(sine(gn, rng.uniform(4000.0, 7000.0)), perc(gn, 0.001, 0.1))
            place(out, g, dt * len(notes) + 0.03 * k + rng.uniform(0, 0.02), 0.12)
    return echo(out, 0.085, 0.3, 0.3, 4000.0, total=len(out) + ns(0.3))


# ---------------------------------------------------------------- combat

def swing(v):
    """Weapon swings. 1 light blade, 2 sword, 3 heavy axe or club."""
    rng = random.Random(4000 + v)
    if v == 1:
        return whoosh(rng, 0.22, 650.0, 2800.0, 1000.0, q=2.4, peak_at=0.4)
    if v == 2:
        w = whoosh(rng, 0.32, 420.0, 1900.0, 520.0, q=1.9, peak_at=0.45)
        n = len(w)
        whistle = env_mul(sine(n, curve(n, [(0, 300.0), (0.14, 900.0), (0.32, 380.0)], exp=True)),
                          swell(n, 0.45, 3.0))
        return [a + 0.08 * b for a, b in zip(w, whistle)]
    w = whoosh(rng, 0.46, 160.0, 900.0, 200.0, q=1.3, peak_at=0.5, power=1.6)
    n = len(w)
    body = env_mul(lp1(white(n, rng), 260.0), swell(n, 0.5, 2.0))
    return [a + 2.5 * b for a, b in zip(w, body)]


def spell(kind):
    """Spell casts: fire, ice, dark, arcane."""
    rng = random.Random({'fire': 5001, 'ice': 5002, 'dark': 5003, 'arcane': 5004}[kind])
    if kind == 'fire':
        dur = 1.0
        n = ns(dur)
        nz = white(n, rng)
        co = curve(n, [(0, 250.0), (0.22, 4200.0), (0.5, 2200.0), (dur, 600.0)], exp=True)
        roar = svf(nz, co, 0.9)
        turb = smooth_random(n, 24.0, rng, 0.55, 1.0)
        env = env_ahr(n, 0.12, 0.15, 0.7)
        body = [a * b * c for a, b, c in zip(roar, turb, env)]
        cr = svf(crackle(n, 70.0, rng, decay=0.003), 3000.0, 0.8, 'bp')
        cre = curve(n, [(0, 0.0), (0.1, 1.0), (0.7, 0.6), (dur, 0.0)])
        whump = thump(110.0, 48.0, 0.5, 0.15)
        launch = env_mul(svf(white(n, rng), curve(n, [(0, 400.0), (0.3, 1800.0)], exp=True), 4.0, 'bp'),
                         swell(n, 0.25, 2.0))
        out = [a + 1.4 * b * c + 0.7 * d for a, b, c, d in zip(body, cr, cre, launch)]
        place(out, whump, 0.05, 0.9)
        return room(drive(out, 1.5), rt60=1.0, wet=0.2, size=0.8)
    if kind == 'ice':
        dur = 1.1
        n = ns(dur)
        out = zeros(n)
        hiss = env_mul(svf(white(n, rng), curve(n, [(0, 9000.0), (dur, 3500.0)], exp=True), 1.5, 'bp'),
                       env_ahr(n, 0.25, 0.1, 0.75))
        place(out, hiss, 0.0, 0.5)
        pitches = [note(x) for x in ('D7', 'E7', 'F7', 'A7', 'C8', 'A6', 'E6')]
        for k in range(16):
            t = 0.03 + 0.55 * (k / 16.0) + rng.uniform(0.0, 0.03)
            f = hz(rng.choice(pitches)) * rng.uniform(0.995, 1.005)
            gn = ns(rng.uniform(0.18, 0.4))
            g = env_mul(sine(gn, f), perc(gn, 0.001, gn / SR))
            place(out, g, t, 0.18 + 0.12 * rng.random())
        pad_n = ns(0.9)
        pd = env_mul([a + 0.6 * b for a, b in zip(tri(pad_n, hz(note('D6'))), tri(pad_n, hz(note('A6'))))],
                     env_ahr(pad_n, 0.3, 0.1, 0.5))
        place(out, pd, 0.05, 0.12)
        tink = metal(rng, 0.6, 3520.0, (1.0, 1.5, 2.33), 0.5)
        place(out, tink, 0.5, 0.25)
        cn = ns(0.16)
        crk = svf(crackle(cn, 1500.0, rng, decay=0.0008), 5000.0, 0.8, 'hp')
        place(out, env_mul(crk, perc(cn, 0.001, 0.16)), 0.5, 0.35)
        return room(echo(out, 0.11, 0.35, 0.35, 6000.0, total=n + ns(0.3)), rt60=1.2, wet=0.18, size=0.9)
    if kind == 'dark':
        dur = 1.25
        n = ns(dur)
        bend = curve(n, [(0, 1.0), (dur, 0.78)], exp=True)
        x = zeros(n)
        for f in (55.0, 58.27, 82.41, 110.6):
            s = saw(n, [f * b for b in bend], rng.random())
            for i in range(n):
                x[i] += s[i]
        co = curve(n, [(0, 160.0), (0.55, 1400.0), (dur, 120.0)], exp=True)
        y = svf(x, co, 3.0)
        w = TAU * curve(n, [(0, 4.0), (dur, 11.0)])[0] / SR
        trem = [0.6 + 0.4 * math.sin(w * i * (1.0 + i / n)) for i in range(n)]
        env = swell(n, 0.55, 1.5)
        body = [a * b * c for a, b, c in zip(y, trem, env)]
        suck = env_mul(svf(white(n, rng), 700.0, 0.8), [(i / n) ** 4 if i < 0.6 * n else 0.0 for i in range(n)])
        suck = [v * (1.0 if i < 0.6 * n - 200 else max(0.0, (0.6 * n - i) / 200.0)) for i, v in enumerate(suck)]
        whisper = env_mul(formants(white(n, rng), [(curve(n, [(0, 900.0), (dur, 1700.0)], exp=True), 6.0, 1.0),
                                                    (2600.0, 8.0, 0.6)]), swell(n, 0.4, 2.0))
        out = [0.25 * a + 0.9 * b + 0.6 * c for a, b, c in zip(body, suck, whisper)]
        place(out, thump(85.0, 32.0, 0.7, 0.2), 0.6, 1.0)
        return room(drive(out, 1.8), rt60=1.3, wet=0.3, size=1.0, damp=3500.0)
    # arcane
    dur = 1.0
    n = ns(dur)
    out = zeros(n)
    sn = ns(0.4)
    fc = curve(sn, [(0, 280.0), (0.35, 1150.0)], exp=True)
    ph = 0.0
    zw = [0.0] * sn
    for i in range(sn):
        ph += TAU * fc[i] / SR
        zw[i] = math.sin(ph + 1.6 * math.sin(2.0 * ph))
    place(out, env_mul(zw, swell(sn, 0.8, 1.0)), 0.0, 0.5)
    arp = [note(x) for x in ('D6', 'F6', 'G#6', 'A6', 'C#7', 'D7')]
    for k, m in enumerate(arp):
        an = ns(0.12)
        a = env_mul(svf(pulse(an, hz(m), 0.125), 7000.0, 0.7), perc(an, 0.001, 0.12))
        place(out, a, 0.28 + 0.032 * k, 0.45)
    hn = ns(0.65)
    held = zeros(hn)
    for m in (note('D6'), note('A6'), note('C#7')):
        s = sine(hn, [hz(m) * (1.0 + 0.004 * math.sin(TAU * 6.0 * i / SR)) for i in range(hn)])
        for i in range(hn):
            held[i] += s[i]
    place(out, env_mul(held, env_ahr(hn, 0.02, 0.1, 0.53)), 0.47, 0.22)
    sp = env_mul(svf(white(ns(0.6), rng), 8500.0, 0.7, 'hp'), swell(ns(0.6), 0.3, 2.0))
    place(out, sp, 0.3, 0.25)
    return room(echo(out, 0.09, 0.42, 0.4, 5000.0, total=n + ns(0.4)), rt60=1.2, wet=0.18, size=0.9)


def hit(v):
    """Hits. 1 body thud, 2 armour clank, 3 heavy bone-crunch."""
    rng = random.Random(6000 + v)
    if v == 1:
        out = zeros(ns(0.3))
        place(out, thump(150.0, 55.0, 0.2, 0.025), 0.0, 1.0)
        place(out, noise_hit(rng, 0.12, 1300.0, 0.7, 'lp', t60=0.08), 0.0, 0.8)
        place(out, noise_hit(rng, 0.04, 900.0, 1.2, t60=0.03), 0.002, 0.7)
        return room(drive(out, 2.5), rt60=0.4, wet=0.12, size=0.5)
    if v == 2:
        out = zeros(ns(0.6))
        place(out, thump(180.0, 70.0, 0.12, 0.02), 0.0, 0.6)
        place(out, metal(rng, 0.55, 510.0, (1.0, 2.32, 3.76, 4.95, 6.1, 7.4), 0.45, 0.01), 0.0, 0.5)
        place(out, noise_hit(rng, 0.02, 4500.0, 0.7, 'hp', t60=0.015), 0.0, 0.6)
        return room(drive(out, 1.8), rt60=0.5, wet=0.14, size=0.6)
    out = zeros(ns(0.4))
    place(out, thump(120.0, 40.0, 0.28, 0.04), 0.0, 1.0)
    cn = ns(0.09)
    crunch = svf(crackle(cn, 4500.0, rng, decay=0.0009), 2400.0, 0.8, 'bp')
    place(out, env_mul(crunch, perc(cn, 0.001, 0.09)), 0.004, 1.3)
    place(out, noise_hit(rng, 0.1, 1800.0, 0.7, 'lp', t60=0.07), 0.0, 0.7)
    return room(drive(out, 3.0), rt60=0.45, wet=0.12, size=0.5)


def miss():
    """A whiff: thin, quick, airy swipe that hits nothing."""
    rng = random.Random(7001)
    a = whoosh(rng, 0.17, 900.0, 3300.0, 1600.0, q=3.2, peak_at=0.35, power=2.4, sheen=0.5)
    b = whoosh(rng, 0.14, 1200.0, 2600.0, 1400.0, q=3.0, peak_at=0.4, power=2.4)
    out = zeros(ns(0.3))
    place(out, a, 0.0, 1.0)
    place(out, b, 0.09, 0.35)
    return out


# ---------------------------------------------------------------- enemies

def growl(v):
    """Growls. 1 large beast (ogre, troll, wolfman), 2 mid (goblin, zombie),
    3 small and snarling (imp, hellhound, spider)."""
    rng = random.Random(8000 + v)
    if v == 1:
        return room(creature(rng, 0.95, [(0, 52.0), (0.18, 74.0), (0.6, 66.0), (0.95, 48.0)],
                             [(0, 380.0), (0.3, 540.0), (0.95, 420.0)], [(0, 760.0), (0.3, 900.0), (0.95, 700.0)],
                             2400.0, rough=0.65, breath=0.35, flutter=0.35, flut_rate=26.0, amt=3.0,
                             q=(4.0, 6.0, 8.0)), rt60=0.7, wet=0.15)
    if v == 2:
        return room(creature(rng, 0.72, [(0, 92.0), (0.15, 122.0), (0.5, 108.0), (0.72, 84.0)],
                             [(0, 600.0), (0.3, 720.0), (0.72, 560.0)], [(0, 1050.0), (0.3, 1200.0), (0.72, 980.0)],
                             2600.0, rough=0.45, breath=0.3, flutter=0.3, flut_rate=31.0, amt=2.6),
                    rt60=0.6, wet=0.15)
    return room(creature(rng, 0.55, [(0, 150.0), (0.1, 215.0), (0.35, 190.0), (0.55, 135.0)],
                         [(0, 520.0), (0.2, 600.0), (0.55, 500.0)], [(0, 1600.0), (0.2, 1850.0), (0.55, 1500.0)],
                         2900.0, rough=0.5, breath=0.55, flutter=0.4, flut_rate=38.0, amt=3.0,
                         env=swell(ns(0.55), 0.18, 1.0)), rt60=0.5, wet=0.15)


def screech(v):
    """Screeches. 1 harpy cry, 2 chittering bat or spider, 3 ghostly wail."""
    rng = random.Random(9000 + v)
    if v == 1:
        x = creature(rng, 0.62, [(0, 880.0), (0.12, 1420.0), (0.4, 1250.0), (0.62, 780.0)],
                     [(0, 900.0), (0.62, 800.0)], [(0, 2300.0), (0.15, 2600.0), (0.62, 2100.0)], 3400.0,
                     rough=0.2, breath=0.5, jitter=0.02, vib=0.035, vib_rate=11.0, amt=2.2,
                     q=(3.0, 5.0, 6.0), gains=(0.7, 1.0, 0.5), env=swell(ns(0.62), 0.15, 1.0))
        return room(x, rt60=0.8, wet=0.18)
    if v == 2:
        out = zeros(ns(0.55))
        for k in range(6):
            d = 0.05 + 0.01 * rng.random()
            f = rng.uniform(1700.0, 2300.0) * (1.0 - 0.05 * k)
            c = creature(rng, d, [(0, f * 0.8), (d * 0.3, f * 1.1), (d, f * 0.85)], 1200.0, 2800.0, 4200.0,
                         rough=0.15, breath=0.6, jitter=0.03, amt=2.0, q=(3.0, 5.0, 6.0),
                         gains=(0.6, 1.0, 0.6), env=swell(ns(d), 0.3, 1.5))
            place(out, c, 0.012 + k * 0.075 + rng.uniform(0.0, 0.012), 1.0 - 0.08 * k)
        return room(out, rt60=0.6, wet=0.15)
    x = creature(rng, 1.0, [(0, 480.0), (0.25, 760.0), (0.6, 690.0), (1.0, 420.0)],
                 [(0, 340.0), (0.5, 420.0), (1.0, 330.0)], [(0, 780.0), (0.5, 950.0), (1.0, 760.0)], 2300.0,
                 rough=0.0, breath=0.7, jitter=0.015, vib=0.025, vib_rate=5.5, amt=1.6,
                 q=(6.0, 8.0, 10.0), gains=(1.0, 0.5, 0.15), env=swell(ns(1.0), 0.3, 1.2))
    y = creature(rng, 1.0, [(0, 720.0), (0.25, 1140.0), (0.6, 1035.0), (1.0, 630.0)],
                 380.0, 1000.0, 2400.0, rough=0.0, breath=0.4, vib=0.03, vib_rate=5.2, amt=1.5,
                 env=swell(ns(1.0), 0.35, 1.5))
    return room([a + 0.4 * b for a, b in zip(x, y)], rt60=1.6, wet=0.32, size=1.1)


def death(v):
    """Death screams. 1 large beast with a body-fall thud, 2 humanoid, 3 small or
    spectral creature dissolving into a hiss."""
    rng = random.Random(10000 + v)
    if v == 1:
        dur = 1.4
        x = creature(rng, dur, [(0, 150.0), (0.1, 190.0), (0.5, 120.0), (dur, 46.0)],
                     [(0, 720.0), (0.4, 650.0), (dur, 430.0)], [(0, 1150.0), (0.4, 1050.0), (dur, 720.0)],
                     2500.0, rough=[(0, 0.3), (dur, 0.85)], breath=0.35, jitter=0.04, flutter=0.5,
                     flut_rate=17.0, amt=3.0, env=env_ahr(ns(dur), 0.04, 0.35, dur - 0.39))
        out = zeros(ns(1.7))
        place(out, x, 0.0, 1.0)
        place(out, thump(90.0, 38.0, 0.35, 0.05), 1.05, 0.3)
        place(out, noise_hit(rng, 0.2, 500.0, 0.7, 'lp', t60=0.15), 1.05, 0.35)
        return room(out, rt60=0.9, wet=0.15)
    if v == 2:
        dur = 1.05
        x = creature(rng, dur, [(0, 300.0), (0.12, 370.0), (0.5, 250.0), (dur, 140.0)],
                     [(0, 760.0), (0.5, 650.0), (dur, 480.0)], [(0, 1250.0), (0.5, 1080.0), (dur, 800.0)],
                     2650.0, rough=[(0, 0.2), (dur, 0.6)], breath=0.3, jitter=0.03, flutter=0.35,
                     flut_rate=20.0, amt=2.6, env=env_ahr(ns(dur), 0.03, 0.3, dur - 0.33))
        return room(x, rt60=0.8, wet=0.15)
    dur = 0.95
    x = creature(rng, dur, [(0, 620.0), (0.1, 720.0), (0.5, 400.0), (dur, 190.0)],
                 [(0, 420.0), (dur, 330.0)], [(0, 2200.0), (0.5, 1500.0), (dur, 850.0)], 3000.0,
                 rough=[(0, 0.1), (dur, 0.5)], breath=0.4, jitter=0.03, vib=0.04, vib_rate=9.0,
                 amt=2.2, env=env_ahr(ns(dur), 0.02, 0.2, dur - 0.22))
    n = ns(1.2)
    diss = env_mul(svf(white(n, rng), curve(n, [(0, 6000.0), (1.2, 900.0)], exp=True), 1.2, 'bp'),
                   curve(n, [(0, 0.0), (0.3, 0.7), (1.2, 0.0)]))
    out = zeros(n)
    place(out, x, 0.0, 1.0)
    place(out, diss, 0.0, 0.5)
    return room(out, rt60=1.3, wet=0.25, size=1.0)


# ---------------------------------------------------------------- environment loops

def _loop_len(seconds):
    n = ns(seconds)
    return n - n % 64


def torch_loop():
    """About 5 s seamless torch: low flame roar with flicker, crackles and pops."""
    rng = random.Random(11001)
    L = _loop_len(5.0)
    mid = white(L, rng)
    side_l = white(L, rng)
    side_r = white(L, rng)
    roar = loop_fx(lambda x: svf(x, 480.0, 0.6), mid)
    body = loop_fx(lambda x: svf(x, 1500.0, 0.8, 'bp'), mid)
    hiss_l = loop_fx(lambda x: svf(x, 5000.0, 0.7, 'hp'), side_l)
    hiss_r = loop_fx(lambda x: svf(x, 5000.0, 0.7, 'hp'), side_r)
    flick = smooth_random(L, 7.0, rng, 0.0, 1.0, wrap=True)
    slow = smooth_random(L, 0.8, rng, 0.0, 1.0, wrap=True)
    left = buf(L)
    right = buf(L)
    for i in range(L):
        am = 0.55 + 0.3 * flick[i] + 0.15 * slow[i]
        b = (1.0 * roar[i] + 0.45 * body[i]) * am
        left[i] = b + 0.05 * hiss_l[i] * am
        right[i] = b + 0.05 * hiss_r[i] * am
    t = 0.0
    while True:
        t += rng.expovariate(14.0)
        if t >= L / SR:
            break
        big = rng.random() < 0.08
        pan = rng.uniform(-0.35, 0.35)
        gl, gr = pan_gains(pan)
        if big:
            n = ns(0.04)
            pop = noise_hit(rng, 0.04, rng.uniform(900.0, 2200.0), 0.9, t60=0.03)
            low = thump(rng.uniform(220.0, 380.0), 120.0, 0.03, 0.005)
            sig = [a + 0.6 * b for a, b in zip(pop, low + [0.0] * (n - len(low)))]
            g = rng.uniform(0.9, 1.3)
        elif rng.random() < 0.3:
            sig = zeros(ns(0.035))
            for k in range(rng.randint(3, 6)):
                place(sig, noise_hit(rng, 0.004, rng.uniform(3000.0, 7000.0), 1.0, t60=0.003),
                      rng.uniform(0.0, 0.028), rng.uniform(0.3, 0.8))
            g = rng.uniform(0.6, 1.1)
        else:
            d = rng.uniform(0.003, 0.012)
            sig = noise_hit(rng, d + 0.002, rng.uniform(1500.0, 6500.0), 1.0, t60=d)
            g = rng.uniform(0.4, 1.2)
        start = ns(t)
        mix_into(left, sig, start, g * gl, wrap=True)
        mix_into(right, sig, start, g * gr, wrap=True)
    return left, right


def ambience_loop():
    """About 30 s seamless dungeon ambience: a low beating drone, moving air, a
    faint wind whistle and distant water drips in a large stone space."""
    rng = random.Random(12001)
    L = _loop_len(30.0)
    secs = L / SR

    def whole(f):
        # snap to a whole number of cycles per loop so oscillators wrap cleanly
        return round(f * secs) / secs

    left = buf(L)
    right = buf(L)
    d1 = sine(L, whole(55.0))
    d2 = sine(L, whole(55.0) + 2.0 / secs)
    d3 = sine(L, whole(82.4))
    sw = loop_fx(lambda x: svf(x, 140.0, 0.7), saw(L, whole(41.2)))
    sin = math.sin
    w1 = TAU / L
    for i in range(L):
        lfo = 0.75 + 0.25 * sin(w1 * i * 2 + 1.0)
        v = (0.5 * d1[i] + 0.4 * d2[i] + 0.18 * d3[i] + 0.35 * sw[i]) * lfo
        left[i] = v
        right[i] = v
    for side, seed in ((left, 1), (right, 2)):
        r2 = random.Random(12001 + seed)
        nz = white(L, r2)
        air = loop_fx(lambda x: svf(x, 650.0, 0.6, 'bp'), nz)
        rumble = loop_fx(lambda x: svf(x, 220.0, 0.7), nz)
        mod = smooth_random(L, 0.18, r2, 0.4, 1.0, wrap=True)
        for i in range(L):
            side[i] += (0.35 * air[i] + 0.5 * rumble[i]) * mod[i]
    wind_n = white(L, rng)
    co = [430.0 * (1.0 + 0.35 * sin(w1 * i * 3)) * (1.0 + 0.1 * sin(w1 * i * 7)) for i in range(L)]
    wind = loop_fx(lambda x: svf(x, co + co, 9.0, 'bp', block=64), wind_n)
    for i in range(L):
        p = sin(w1 * i * 2 + 0.5)
        g = 0.12 * (0.6 + 0.4 * sin(w1 * i * 5))
        left[i] += wind[i] * g * (1.0 - 0.5 * p)
        right[i] += wind[i] * g * (1.0 + 0.5 * p)

    send = buf(L)
    t = 0.7
    while t < secs - 0.2:
        f = rng.uniform(1100.0, 2300.0)
        for k in range(2 if rng.random() < 0.3 else 1):
            dn = ns(0.12)
            ff = curve(dn, [(0, f * 0.7), (0.008, f), (0.07, f * 1.28)], exp=True)
            d = env_mul(sine(dn, ff), perc(dn, 0.0008, 0.09))
            g = rng.uniform(0.25, 0.5) * (0.6 if k else 1.0)
            pan = rng.uniform(-0.8, 0.8)
            gl, gr = pan_gains(pan)
            st = ns(t + k * rng.uniform(0.12, 0.25))
            mix_into(left, d, st, g * gl * 0.35, wrap=True)
            mix_into(right, d, st, g * gr * 0.35, wrap=True)
            mix_into(send, d, st, g, wrap=True)
            f *= 1.08
        t += rng.uniform(1.6, 4.2)
    rl, rr = loop_fx(lambda x: reverb(x, 3.4, 1.6, 3800.0, 0.03), send)
    el, er = loop_fx(lambda x: (echo(x, 0.23, 0.35, 1.0, 2500.0), echo(x, 0.31, 0.3, 1.0, 2500.0)), send)
    for i in range(L):
        left[i] += 0.9 * rl[i] + 0.06 * (el[i] - send[i])
        right[i] += 0.9 * rr[i] + 0.06 * (er[i] - send[i])
    return left, right


# ---------------------------------------------------------------- UI

def ui(kind):
    """Menu move tick, button click, confirm and cancel."""
    rng = random.Random({'move': 13001, 'click': 13002, 'confirm': 13003, 'cancel': 13004}[kind])
    if kind == 'move':
        n = ns(0.06)
        f = curve(n, [(0, 1480.0), (0.03, 1320.0)], exp=True)
        x = svf(pulse(n, f, 0.25), 5000.0, 0.7)
        e = perc(n, 0.001, 0.05)
        out = [a * b for a, b in zip(x, e)]
        place(out, env_mul(sine(ns(0.03), 2960.0), perc(ns(0.03), 0.0005, 0.02)), 0.0, 0.25)
        return out + zeros(ns(0.02))
    if kind == 'click':
        n = ns(0.07)
        x = svf(pulse(n, curve(n, [(0, 900.0), (0.04, 760.0)], exp=True), 0.5), 3500.0, 0.7)
        out = env_mul(x, perc(n, 0.0008, 0.045))
        place(out, noise_hit(rng, 0.008, 3500.0, 0.8, 'hp', t60=0.006), 0.0, 0.6)
        place(out, thump(320.0, 180.0, 0.04, 0.01), 0.0, 0.5)
        return out + zeros(ns(0.02))
    if kind == 'confirm':
        out = zeros(ns(0.3))
        for k, (nm, ln) in enumerate((('A5', 0.07), ('E6', 0.2))):
            n = ns(ln)
            f = hz(note(nm))
            x = svf(pulse(n, f, 0.25), 6000.0, 0.7)
            y = tri(n, f * 0.5)
            place(out, env_mul([a + 0.6 * b for a, b in zip(x, y)], perc(n, 0.002, ln)), 0.065 * k,
                  0.85 if k == 0 else 1.0)
        return echo(out, 0.07, 0.25, 0.25, 4500.0, total=len(out) + ns(0.12))
    out = zeros(ns(0.26))
    for k, (nm, ln) in enumerate((('E5', 0.07), ('B4', 0.17))):
        n = ns(ln)
        f = hz(note(nm))
        x = svf(pulse(n, f, 0.5), 2600.0, 0.7)
        y = tri(n, f * 0.5)
        place(out, env_mul([a + 0.7 * b for a, b in zip(x, y)], perc(n, 0.002, ln)), 0.07 * k, 1.0)
    return echo(out, 0.06, 0.2, 0.2, 3000.0, total=len(out) + ns(0.1))
