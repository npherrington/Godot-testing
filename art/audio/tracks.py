"""The music. Every melody, bass line and progression here is an original
composition for this game. Each function returns (left, right, song)."""

import random

from dsp import note
from music import (Chords, Kit, Song, Voice, bell, brass, choir, lead, pad, pluck, poly,
                   saw_bass, soft_tri, tri_bass)


# ---------------------------------------------------------------- exploration

def main_loop():
    """Dungeon-crawl theme. D minor (Aeolian, Dorian B in bar 4), 92 BPM, 24 bars.
    A (soft flute lead) - B (lyrical, counter-line) - A' (full band, counter-line)."""
    s = Song(bpm=92, bars=24, seed=101)
    ch = Chords("Dm | Bb | C | Am | Dm | Bb | Gm | A | "
                "Gm | Dm | Bb | F | Gm | Dm | Bb C | A7 | "
                "Dm | Bb | C | Am | Dm | Bb | Gm | A7")
    A = ("A4/2 D5/2 E5/2 F5/6 E5/2 D5/2 | D5/6 C5/2 Bb4/4 F4/4 | G4/2 C5/2 D5/2 E5/6 D5/2 C5/2 | "
         "E5/6 D5/2 C5/4 B4/4 | A4/2 D5/2 E5/2 F5/6 G5/2 A5/2 | Bb5/6 A5/2 G5/4 F5/4 | "
         "E5/4 G5/4 F5/2 E5/2 D5/4 | ")
    B = ("Bb4/6 C5/2 D5/8 | F5/6 E5/2 D5/4 A4/4 | Bb4/6 C5/2 D5/4 F5/4 | A5/8 G5/4 F5/4 | "
         "G5/6 F5/2 E5/4 D5/4 | F5/6 E5/2 D5/4 C5/4 | D5/4 Bb4/4 C5/4 E5/4 | "
         "A4/2 C#5/2 E5/2 G5/2 F5/2 E5/2 D5/2 C#5/2 |")
    counter_b = ("D4/8 G4/4 Bb4/4 | A4/8 F4/8 | D4/8 Bb3/4 D4/4 | C5/8 A4/8 | "
                 "Bb4/8 G4/8 | A4/8 F4/8 | F4/8 G4/8 | E4/8 C#4/8 |")
    counter_a = ("F4/8 A4/4 F4/4 | F4/8 D4/8 | E4/8 G4/4 E4/4 | C4/8 E4/8 | "
                 "F4/8 A4/4 D5/4 | D5/8 Bb4/4 D5/4 | G4/8 Bb4/8 | A4/8 E4/8 |")

    flute = Voice(s, lead, 'flute', gain=0.26, pan=0.1, rev=0.32, dly=0.16, duty=0.5,
                  bright=2600.0, vib=9.0, pwm=0.0, a=0.02, s=0.7)
    ld = Voice(s, lead, 'lead', gain=0.27, pan=0.12, rev=0.24, dly=0.16, duty=0.25)
    ctr = Voice(s, lead, 'counter', gain=0.12, pan=-0.35, rev=0.26, duty=0.5, bright=2200.0,
                vib=6.0, scoop=0.0, pwm=0.0, a=0.015, s=0.75)
    bass = Voice(s, tri_bass, 'bass', gain=0.5, gate=0.9)
    pd = Voice(s, pad, 'pad', gain=0.13, rev=0.45, cutoff=1100.0)
    arp = Voice(s, pluck, 'arp', gain=0.1, pan=0.3, rev=0.2, dly=0.35, t60=0.3, bright=4200.0)
    kit = Kit(s, seed=7, kick={'hi': 120.0, 'lo': 44.0, 't60': 0.38, 'click': 0.15},
              snare={'tone': 200.0, 't_noise': 0.16}, gain=0.85)

    flute.line(0, A + "E5/4 C#5/4 A4/8 |")
    ld.line(8, B)
    ctr.line(8, counter_b)
    ld.line(16, A + "E5/2 F5/2 E5/2 D5/2 C#5/8 |")
    ctr.line(16, counter_a)

    bass.bass(ch, 0, 8, "R/6 R/2 O/4 5/4")
    bass.bass(ch, 8, 16, "R/4 5/4 O/4 5/4")
    bass.bass(ch, 16, 24, "R/2 R/2 O/2 R/2 5/2 R/2 O/2 5/2")
    pd.chords(ch, 0, 24, lo=50, hi=69)
    arp.arp(ch, 16, 24, [0, 1, 2, 3, 2, 1], rate=1.0, lo=62)

    for b in range(0, 8):
        kit.bar(b, {'k': "x.......x.......", 'h': "..o...o...o...o."})
    for b in range(8, 16):
        kit.bar(b, {'k': "x.......x.x.....", 'r': "........x.......", 'h': "x.o.x.o.x.o.x.o."})
    for b in range(16, 23):
        kit.bar(b, {'k': "x.....x...x.....", 's': "....x.......x...", 'h': "xoxoxoxoxoxoxoxo"})
    kit.bar(23, {'k': "x.....x.........", 's': "....x...o.o.x.xx", 'h': "xoxoxoxo........"})
    kit.bar(8, {'c': "x..............."})
    kit.bar(16, {'c': "x..............."})

    L, R = s.mixdown(rt60=2.4, size=1.2, damp=4500.0, rev_gain=0.9, dly_steps=3, dly_fb=0.36)
    return L, R, s


# ---------------------------------------------------------------- battle

def battle_loop():
    """Battle theme. D minor, 152 BPM, 32 bars. A riff (galloping bass, chord stabs) -
    B descending D-C-Bb-A melody - C main-theme motif with a Neapolitan Eb - D build
    with 16th bass, arpeggios and a snare roll back into the riff."""
    s = Song(bpm=152, bars=32, seed=202)
    ch = Chords("Dm | Dm | Bb | C | Dm | Dm | Bb | A | "
                "Dm | C | Bb | A | Dm | C | Bb | A | "
                "Gm | Dm | Bb | A | Gm | Dm | Eb | A | "
                "Bb | C | Dm | Dm | Bb | C | A | A")
    riff = ("A4/1 D5/1 E5/1 F5/3 E5/2 D5/2 A4/2 D5/2 F5/2 | E5/3 D5/3 C5/2 D5/8 | "
            "A4/1 D5/1 F5/1 G5/3 F5/2 D5/2 Bb4/2 D5/2 F5/2 | G5/3 F5/3 E5/2 C5/4 E5/4 | "
            "A4/1 D5/1 E5/1 F5/3 E5/2 D5/2 A4/2 D5/2 F5/2 | E5/3 D5/3 C5/2 D5/4 F5/4 | "
            "G5/3 F5/3 D5/2 Bb5/4 A5/4 | A5/6 G5/2 F5/2 E5/2 C#5/4 |")
    mel_b = ("F5/6 E5/2 D5/4 A5/4 | G5/6 F5/2 E5/4 C5/4 | D5/6 E5/2 F5/4 G5/4 | A5/8 C#5/4 E5/4 | "
             "F5/6 E5/2 D5/4 A5/4 | G5/6 A5/2 G5/4 E5/4 | F5/4 D5/4 Bb5/4 A5/4 | "
             "A5/4 G5/2 F5/2 E5/2 D5/2 C#5/4 |")
    mel_c = ("D5/2 G5/2 A5/2 Bb5/6 A5/2 G5/2 | F5/6 E5/2 D5/4 A4/4 | D5/2 F5/2 G5/2 A5/6 G5/2 F5/2 | "
             "E5/6 C#5/2 A4/8 | D5/2 G5/2 A5/2 Bb5/6 C6/2 D6/2 | A5/6 F5/2 D5/4 F5/4 | "
             "G5/4 Bb5/4 Eb6/4 D6/2 Bb5/2 | C#6/8 A5/4 E5/4 |")
    mel_d = ("D5/3 F5/3 Bb5/2 r/2 A5/2 G5/2 F5/2 | E5/3 G5/3 C6/2 r/2 Bb5/2 A5/2 G5/2 | "
             "A5/3 F5/3 D5/2 E5/2 F5/2 G5/2 A5/2 | D6/8 C6/4 A5/4 | "
             "D5/3 F5/3 Bb5/2 r/2 A5/2 G5/2 F5/2 | E5/3 G5/3 C6/2 r/2 Bb5/2 A5/2 G5/2 | "
             "C#6/3 A5/3 E5/2 C#5/2 E5/2 A5/2 C#6/2 | A5/4 G5/2 F5/2 E5/2 D5/2 C#5/2 E5/2 |")
    ctr_b = ("A4/8 F4/8 | E4/8 G4/8 | F4/8 D4/8 | C#5/8 A4/8 | "
             "A4/8 F4/8 | E4/8 C5/8 | D4/8 F4/8 | E4/8 C#4/8 |")
    ctr_c = ("G4/8 Bb4/8 | A4/8 F4/8 | F4/8 D4/8 | A3/8 C#4/8 | "
             "G4/8 Bb4/8 | F4/8 A4/8 | Eb4/8 G4/8 | E4/8 A4/8 |")

    ld = Voice(s, lead, 'lead', gain=0.26, pan=0.1, rev=0.15, dly=0.1, duty=0.25, a=0.003,
               bright=5200.0, vib=14.0, rate=6.0, d=0.2, s=0.7, scoop=-12.0)
    ctr = Voice(s, lead, 'counter', gain=0.16, pan=-0.35, rev=0.18, duty=0.5, bright=2800.0,
                vib=8.0, scoop=0.0, pwm=0.0)
    stab = Voice(s, poly(pluck), 'stabs', gain=0.32, pan=-0.2, rev=0.12, duty=0.25, t60=0.14,
                 bright=3500.0)
    bass = Voice(s, saw_bass, 'bass', gain=0.5, gate=0.8)
    pd = Voice(s, pad, 'pad', gain=0.09, rev=0.3, cutoff=1500.0, a=0.3, r=0.6)
    arp = Voice(s, pluck, 'arp', gain=0.08, pan=0.35, rev=0.1, dly=0.3, t60=0.18)
    kit = Kit(s, seed=8, kick={'hi': 165.0, 'lo': 48.0, 't60': 0.33, 'click': 0.35},
              snare={'tone': 195.0, 't_noise': 0.19})

    ld.line(0, riff)
    ld.line(8, mel_b)
    ld.line(16, mel_c)
    ld.line(24, mel_d)
    ctr.line(8, ctr_b)
    ctr.line(16, ctr_c)
    stab.stabs(ch, 0, 8, "..x...x...x...x.", lo=57, hi=72)
    stab.stabs(ch, 24, 32, "x..x..x...x..x..", lo=57, hi=72)
    gallop = "R/2 R/1 R/1 R/2 R/1 R/1 O/2 R/1 R/1 5/2 R/2"
    bass.bass(ch, 0, 8, gallop, lo=33)
    bass.bass(ch, 8, 16, "R/2 O/2 R/2 O/2 R/2 O/2 R/2 O/2", lo=33)
    bass.bass(ch, 16, 24, gallop, lo=33)
    bass.bass(ch, 24, 32, "R/1 R/1 O/1 R/1 " * 4, lo=33)
    pd.chords(ch, 8, 24, lo=52, hi=70)
    arp.arp(ch, 26, 32, [0, 1, 2, 3, 4, 3, 2, 1], rate=1.0, lo=62)

    for b in range(0, 8):
        kit.bar(b, {'k': "x.....x.x.....x.", 's': "....x.......x...", 'h': "xoxoxoxoxoxoxoxo"})
    for b in range(8, 16):
        kit.bar(b, {'k': "x...x...x...x...", 's': "....x.......x...", 'h': "x...x...x...x...",
                    'H': "..x...x...x...x."})
    for b in range(16, 24):
        kit.bar(b, {'k': "x.....x...x.....", 's': "....x.......x..o", 'h': "xoxoxoxoxoxoxoxo"})
    for b in range(24, 30):
        kit.bar(b, {'k': "x...x...x...x...", 's': "....x.......x...", 'h': "xoxoxoxoxoxoxoxo"})
    kit.bar(30, {'k': "x.x.x.x.x.x.x.x.", 's': "....x.......x...", 'h': "xoxoxoxoxoxoxoxo"})
    kit.bar(31, {'k': "x.x.x.x.x.......", 's': "o.o.x.o.xoxoxxXX", 't': "........x.x.....",
                 'T': "............x.x."})
    for b in (0, 8, 16, 24):
        kit.bar(b, {'c': "X..............."})

    L, R = s.mixdown(rt60=1.6, size=1.0, damp=5000.0, rev_gain=0.8, dly_steps=3, dly_fb=0.3)
    return L, R, s


# ---------------------------------------------------------------- boss

def boss_loop():
    """Boss theme. E Phrygian (F natural, with Bb tritone and B major dominant),
    132 BPM, 32 bars, 3+3+2 kick and bass. A brass theme over choir - B rising
    line Am-Bb-C-B - C half-time breakdown with tolling bells - D climax."""
    s = Song(bpm=132, bars=32, seed=303)
    ch = Chords("Em | F | Em | F | Em | G | F | Em | "
                "Am | Bb | Am | Bb | C | B | C | B | "
                "Em | Em | C | C | Am | Am | F | B | "
                "Em | F | G | F | Em | F | Bb | B")
    mel_a = ("E5/6 F5/2 E5/4 B4/4 | C5/6 B4/2 A4/4 C5/4 | E5/6 F5/2 E5/4 G5/4 | F5/8 E5/4 C5/4 | "
             "B5/6 C6/2 B5/4 G5/4 | D6/6 C6/2 B5/4 G5/4 | A5/4 C6/4 B5/4 A5/4 | G5/6 F5/2 E5/8 |")
    mel_b = ("A4/2 C5/2 E5/2 A5/6 G5/2 E5/2 | F5/6 D5/2 Bb4/8 | A4/2 C5/2 E5/2 A5/6 B5/2 C6/2 | "
             "D6/6 C6/2 Bb5/4 F5/4 | E5/4 G5/4 C6/4 B5/2 G5/2 | F#5/6 D#5/2 B4/8 | "
             "G5/4 C6/4 E6/4 D6/2 C6/2 | B5/6 A5/2 F#5/4 D#5/4 |")
    mel_d = ("E5/6 F5/2 E5/4 B5/4 | C6/6 B5/2 A5/4 F5/4 | D6/6 C6/2 B5/4 G5/4 | A5/6 G5/2 F5/4 C5/4 | "
             "E5/2 G5/2 B5/2 E6/6 D6/2 B5/2 | C6/6 B5/2 A5/4 F5/4 | Bb5/6 A5/2 F5/4 D5/4 | "
             "B5/4 A5/2 G5/2 F#5/2 E5/2 D#5/4 |")
    bells_c = "B4/16 | G4/16 | E4/8 G4/8 | C5/16 | E5/8 C5/8 | A4/16 | A4/8 C5/8 | B4/8 D#5/8 |"
    ctr_b = ("C4/8 E4/8 | D4/8 F4/8 | C4/8 E4/8 | D4/8 F4/8 | "
             "E4/8 G4/8 | D#4/8 F#4/8 | E4/8 G4/8 | D#4/8 F#4/8 |")
    ctr_d = ("G4/8 B4/8 | A4/8 F4/8 | B4/8 G4/8 | C5/8 A4/8 | "
             "B4/8 G4/8 | A4/8 C5/8 | D5/8 Bb4/8 | D#5/8 F#4/8 |")

    br = Voice(s, brass, 'brass', gain=0.42, pan=0.05, rev=0.25, dly=0.08)
    chip = Voice(s, lead, 'chip', gain=0.07, pan=0.3, rev=0.2, duty=0.125, bright=6000.0)
    ctr = Voice(s, lead, 'counter', gain=0.13, pan=-0.35, rev=0.2, duty=0.5, bright=2400.0,
                vib=7.0, scoop=0.0, pwm=0.0)
    cho = Voice(s, choir, 'choir', gain=0.25, rev=0.45)
    bass = Voice(s, saw_bass, 'bass', gain=0.5, gate=0.85, cut=200.0, env_amt=1400.0, amt=2.6)
    drone = Voice(s, saw_bass, 'drone', gain=0.3, gate=0.98, cut=140.0, env_amt=500.0,
                  env_t=0.4, amt=1.8, d=2.0, s=0.7)
    gl = Voice(s, bell, 'bells', gain=0.3, pan=-0.15, rev=0.5, dly=0.15, kind='glass', t60=2.6)
    toll = Voice(s, bell, 'toll', gain=0.55, pan=0.1, rev=0.5, kind='church', t60=5.0)
    arp = Voice(s, pluck, 'arp', gain=0.065, pan=0.4, rev=0.12, dly=0.25, t60=0.16)
    kit = Kit(s, seed=9, kick={'hi': 140.0, 'lo': 42.0, 't60': 0.5, 'click': 0.3, 'amt': 2.2},
              snare={'tone': 170.0, 't_tone': 0.14, 't_noise': 0.26}, rev=0.18,
              levels={'k': 0.45})

    br.line(0, mel_a)
    br.line(8, mel_b)
    chip.line(8, mel_b, transpose=12)
    gl.line(16, bells_c)
    br.line(24, mel_d)
    chip.line(24, mel_d, transpose=12)
    ctr.line(8, ctr_b)
    ctr.line(24, ctr_d)
    cho.chords(ch, 0, 8, lo=52, hi=71)
    cho.chords(ch, 16, 24, lo=52, hi=71)
    cho.chords(ch, 24, 32, lo=55, hi=74, vel=0.8)
    tres = "R/3 R/3 R/2 R/3 R/3 O/2"
    bass.bass(ch, 0, 16, tres, lo=31)
    drone.bass(ch, 16, 22, "R/16", lo=31)
    bass.bass(ch, 22, 24, tres, lo=31)
    bass.bass(ch, 24, 32, "R/3 O/3 R/2 R/3 O/3 R/2", lo=31)
    arp.arp(ch, 24, 32, [0, 2, 1, 3, 2, 4, 3, 1], rate=1.0, lo=64)
    for b in (16, 18, 20, 22):
        toll.play(b * 16, 16, note('E3'))
    toll.play(0, 16, note('E3'), vel=0.8)

    tres_k = "x..x..x.x..x..x."
    for b in range(0, 8):
        kit.bar(b, {'k': tres_k, 's': "....x.......x...", 'h': "x.x.x.x.x.x.x.x."})
    for b in range(8, 15):
        kit.bar(b, {'k': tres_k, 's': "....x.......x...", 'h': "xoxoxoxoxoxoxoxo"})
    kit.bar(15, {'k': tres_k, 's': "....x.......x.xx", 'h': "xoxoxoxoxoxo....",
                 't': "........x.x....."})
    for b in range(16, 22):
        kit.bar(b, {'B': "x.......x.......", 's': "........x......."})
    kit.bar(22, {'k': tres_k, 'T': "x...x...x...x...", 's': "........x......."})
    kit.bar(23, {'k': tres_k, 't': "x.x.x.x.........", 'T': "........x.x.x.x.",
                 's': "............oxxX"})
    for b in range(24, 31):
        kit.bar(b, {'k': tres_k, 's': "....x.......x...", 'h': "xoxoxoxoxoxoxoxo"})
    kit.bar(31, {'k': "x..x..x.x..x....", 's': "....x.......xxXX", 'h': "xoxoxoxoxoxo...."})
    for b in (0, 8, 24):
        kit.bar(b, {'c': "X...............", 'B': "x..............."})

    L, R = s.mixdown(rt60=2.2, size=1.3, damp=4200.0, rev_gain=0.9, dly_steps=3, dly_fb=0.3)
    return L, R, s


# ---------------------------------------------------------------- victory

def victory_fanfare():
    """Victory jingle, 120 BPM, about 5.6 s, no loop. A D-minor run up, then a
    Bb - C - D major cadence (the dark key lifting to major on the last chord)."""
    s = Song(bpm=120, bars=2, loop=False, tail=1.6, seed=404)
    ld = Voice(s, lead, 'lead', gain=0.3, pan=0.1, rev=0.25, dly=0.12, duty=0.25, a=0.003,
               bright=5200.0, vib=16.0, rate=6.0, scoop=-12.0)
    c1 = Voice(s, lead, 'counter', gain=0.2, pan=-0.3, rev=0.25, duty=0.5, bright=3000.0,
               scoop=0.0, pwm=0.0)
    c2 = Voice(s, lead, 'third', gain=0.16, pan=0.35, rev=0.25, duty=0.5, bright=2600.0,
               scoop=0.0, pwm=0.0)
    br = Voice(s, poly(brass), 'brass', gain=0.32, rev=0.3, a=0.02, r=0.5)
    bass = Voice(s, tri_bass, 'bass', gain=0.5, r=0.4)
    sp = Voice(s, pluck, 'sparkle', gain=0.12, pan=0.4, rev=0.3, dly=0.3, t60=0.25)
    kit = Kit(s, seed=10, kick={'hi': 150.0, 'lo': 46.0, 't60': 0.4})

    ld.line(0, "A4/1 D5/1 F5/1 A5/1 Bb5/3 A5/1 C6/3 Bb5/1 D6/16 r/4")
    c1.line(0, "r/4 F5/3 F5/1 G5/3 G5/1 F#5/16 r/4")
    c2.line(0, "r/4 D5/3 D5/1 E5/3 E5/1 A5/16 r/4")
    br.play(4, 4, [note('Bb3'), note('D4'), note('F4')])
    br.play(8, 4, [note('C4'), note('E4'), note('G4')])
    br.play(12, 16, [note('D4'), note('F#4'), note('A4'), note('D5')])
    bass.line(0, "D3/4 Bb2/4 C3/4 D2/16 r/4")
    sp.line(0, "r/12 D6/1 F#6/1 A6/1 D7/1 A6/1 F#6/1 A6/1 D7/1 F#7/1 D7/1 A6/1 F#6/1 D6/4 r/4")
    kit.bar(0, {'s': "oox.............", 'k': "....x...x...x...", 'c': "....x.......X...",
                'T': "....x...x......."})
    kit.bar(0, {'B': "............x..."})

    L, R = s.mixdown(rt60=2.0, size=1.1, damp=5000.0, rev_gain=0.9, dly_steps=3, dly_fb=0.3)
    return L, R, s


# ---------------------------------------------------------------- ambient

def ambient_crypt():
    """Sparse crypt ambience. D minor, 64 BPM, 16 bars. Slow pad chords two bars
    each, a glass-bell melody with long echoes, a flute counter-line in the second
    half, and a faint wordless choir."""
    s = Song(bpm=64, bars=16, seed=505)
    ch = Chords("Dm9 | Dm9 | Bbmaj7 | Bbmaj7 | Gm6 | Gm6 | A7sus4 | A | "
                "Dm9 | Dm9 | Fmaj7 | Fmaj7 | Gm6 | Gm6 | A7sus4 | A")
    mel = ("r/8 A5/4 E5/4 | F5/12 r/4 | r/8 D6/4 C6/4 | A5/16 | r/8 G5/4 Bb5/4 | A5/12 r/4 | "
           "r/8 E5/4 D5/4 | C#5/16 | r/8 A5/4 E5/4 | F5/12 r/4 | r/8 C6/4 A5/4 | E5/16 | "
           "r/8 D5/4 G5/4 | Bb5/12 r/4 | r/8 D5/4 E5/4 | C#5/16 |")
    flute_line = "D4/16 | E4/8 F4/8 | C4/16 | E4/16 | D4/16 | Bb3/8 D4/8 | D4/16 | C#4/16 |"

    pd = Voice(s, pad, 'pad', gain=0.2, rev=0.55, cutoff=900.0, a=2.0, r=2.5, lfo=0.07, depth=0.35)
    gl = Voice(s, bell, 'bell', gain=0.3, pan=0.2, rev=0.5, dly=0.4, kind='glass', t60=3.0)
    fl = Voice(s, soft_tri, 'flute', gain=0.19, pan=-0.3, rev=0.45, dly=0.1, a=0.25, r=1.2)
    bass = Voice(s, tri_bass, 'bass', gain=0.3, steps=0, a=0.4, s=0.75, r=1.5, sub=0.6)
    cho = Voice(s, choir, 'choir', gain=0.09, rev=0.6, vowel='oo', a=2.5, r=3.0)

    pd.chords(ch, 0, 16, lo=50, hi=70)
    gl.line(0, mel)
    fl.line(8, flute_line)
    bass.bass(ch, 0, 16, "R/16", lo=38)
    cho.chords(ch, 8, 16, lo=57, hi=74)

    L, R = s.mixdown(rt60=4.2, size=1.5, damp=3500.0, rev_gain=1.0, dly_steps=6, dly_fb=0.45,
                     dly_lp=2600.0)
    return L, R, s


def ambient_caverns():
    """Cavern ambience. A Aeolian, 80 BPM, 16 bars. A dark breathing pad and low
    drone, seeded random pentatonic plucks echoing like drips, and a low flute line
    in the second half."""
    s = Song(bpm=80, bars=16, seed=606)
    ch = Chords("Am | Am | Am | Am | Fmaj7 | Fmaj7 | Fmaj7 | Fmaj7 | "
                "Dm7 | Dm7 | Dm7 | Dm7 | Esus4 | Esus4 | Em | Em")
    pd = Voice(s, pad, 'pad', gain=0.24, rev=0.5, cutoff=620.0, q=1.1, a=3.0, r=3.0, lfo=0.05,
               depth=0.45)
    drone = Voice(s, tri_bass, 'drone', gain=0.4, steps=0, a=1.5, s=0.8, r=2.5, sub=0.7)
    fl = Voice(s, soft_tri, 'flute', gain=0.15, pan=0.25, rev=0.5, dly=0.15, a=0.3, r=1.5)
    pd.chords(ch, 0, 16, lo=48, hi=67)
    drone.line(0, "A2/64 F2/64 D2/64 E2/64")
    fl.line(8, "F4/16 | E4/8 D4/8 | C4/16 | A3/16 | B3/16 | A3/8 B3/8 | E4/16 | B3/16 |")

    rng = random.Random(6061)
    scale = {
        'Am': ['A4', 'C5', 'E5', 'G5', 'A5', 'D5'],
        'Fmaj7': ['A4', 'C5', 'E5', 'F5', 'A5', 'G5'],
        'Dm7': ['A4', 'C5', 'D5', 'F5', 'A5', 'E5'],
        'Esus4': ['A4', 'B4', 'E5', 'B5', 'D5', 'E5'],
        'Em': ['B4', 'D5', 'E5', 'G5', 'B5', 'A4'],
    }
    gap = 0
    for slot in range(0, s.steps, 2):
        gap += 1
        if gap >= 3 and rng.random() < 0.2:
            sym = ch.at(slot)[4]
            m = note(rng.choice(scale[sym]))
            sig = pluck(m, s.step * 2, 0.5 + 0.5 * rng.random(), rng, duty=0.25, t60=0.7,
                        bright=2600.0)
            s.put(slot, sig, 0.4, rng.uniform(-0.6, 0.6), 0.4, 0.5, 'plucks')
            gap = 0

    L, R = s.mixdown(rt60=3.6, size=1.4, damp=3000.0, rev_gain=1.0, dly_steps=6, dly_fb=0.5,
                     dly_lp=2400.0)
    return L, R, s


def ambient_depths():
    """Deep ambience. C# Phrygian, 56 BPM, 12 bars. Pad chords C#m - D - A - G#dim
    (three bars each) over a sub drone, a slow choir line, and a distant church
    bell at each chord change."""
    s = Song(bpm=56, bars=12, seed=707)
    pd = Voice(s, pad, 'pad', gain=0.2, rev=0.55, cutoff=700.0, q=0.9, a=3.5, r=3.5, lfo=0.06)
    sub = Voice(s, tri_bass, 'sub', gain=0.3, steps=0, a=2.0, s=0.85, r=3.0, sub=0.8)
    cho = Voice(s, choir, 'choir', gain=0.2, rev=0.6, vowel='oo', a=1.5, r=2.5)
    toll = Voice(s, bell, 'toll', gain=0.55, pan=-0.2, rev=0.7, kind='church', t60=7.0)
    gl = Voice(s, bell, 'glass', gain=0.1, pan=0.4, rev=0.7, dly=0.3, kind='glass', t60=3.5)

    chords = (['C#3', 'G#3', 'C#4', 'E4'], ['D3', 'A3', 'D4', 'F#4'],
              ['A2', 'E3', 'C#4', 'E4'], ['G#2', 'D3', 'G#3', 'B3'])
    for k, c in enumerate(chords):
        pd.play(k * 48, 48, [note(x) for x in c])
        toll.play(k * 48, 16, note(c[0]) + 12 if k else note('C#3'), vel=1.0 if k % 2 == 0 else 0.8)
    sub.line(0, "C#2/48 D2/48 A1/48 G#1/48")
    cho.line(0, "r/8 E4/8 | G#4/16 | F#4/8 E4/8 | F#4/16 | A4/8 F#4/8 | D4/16 | "
                "E4/16 | C#4/8 E4/8 | A3/16 | D4/16 | B3/8 D4/8 | C#4/16 |")
    gl.line(0, "r/16 | r/8 G#5/8 | r/16 | r/16 | r/8 F#5/8 | r/16 | r/16 | r/8 E5/8 | r/16 | "
               "r/16 | r/8 D6/8 | r/16 |")

    L, R = s.mixdown(rt60=5.0, size=1.6, damp=3000.0, rev_gain=1.0, dly_steps=8, dly_fb=0.4,
                     dly_lp=2200.0)
    return L, R, s
