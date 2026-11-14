#!/usr/bin/env python3
"""Build every sound effect and music track from scratch.

    python3 art/audio/build_audio.py                  # rebuild everything
    python3 art/audio/build_audio.py --only sfx_ui_click
    python3 art/audio/build_audio.py --only 'sfx_enemy_*' --levels

Writes 16-bit stereo WAVs to art/out/audio/ (intermediate, gitignored) and
Ogg Vorbis to assets/sounds/sfx/ and assets/sounds/music/. Pure stdlib + ffmpeg.
"""

import sys

sys.dont_write_bytecode = True  # keep __pycache__ out of the repo

import argparse
import fnmatch
import math
import os
import shutil
import subprocess
import time
import wave
from array import array
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent.parent
sys.path.insert(0, str(HERE))

import dsp  # noqa: E402
import music  # noqa: E402
import sfx  # noqa: E402
import tracks  # noqa: E402

WAV_DIR = ROOT / 'art' / 'out' / 'audio'
OUT_DIRS = {'sfx': ROOT / 'assets' / 'sounds' / 'sfx', 'music': ROOT / 'assets' / 'sounds' / 'music'}
FFMPEG = shutil.which('ffmpeg') or '/opt/homebrew/bin/ffmpeg'

PEAK = 10 ** (-1.0 / 20)       # -1 dBFS ceiling for everything
SFX_CAP = -11.0                # loudest 400 ms of a one-shot, LUFS
FOOTSTEP_CAP = -17.0           # footsteps repeat constantly, so they sit lower
UI_CAP = -15.0

# name: (builder, policy). Policies:
#   ('oneshot', cap)   trim, fade, peak to -1 dBFS, then cap the momentary loudness
#   ('loop', lufs)     exact-length seamless loop, integrated loudness target
#   ('music', lufs)    non-looping music, integrated loudness target, fade-out
JOBS = {
    'sfx_player_footstep_1': (lambda: sfx.footstep(1), ('oneshot', FOOTSTEP_CAP)),
    'sfx_player_footstep_2': (lambda: sfx.footstep(2), ('oneshot', FOOTSTEP_CAP)),
    'sfx_player_footstep_3': (lambda: sfx.footstep(3), ('oneshot', FOOTSTEP_CAP)),
    'sfx_player_footstep_4': (lambda: sfx.footstep(4), ('oneshot', FOOTSTEP_CAP)),
    'sfx_player_attack_1': (lambda: sfx.player_attack(1), ('oneshot', SFX_CAP)),
    'sfx_player_attack_2': (lambda: sfx.player_attack(2), ('oneshot', SFX_CAP)),
    'sfx_player_pickup_1': (lambda: sfx.pickup(1), ('oneshot', UI_CAP)),
    'sfx_player_pickup_2': (lambda: sfx.pickup(2), ('oneshot', UI_CAP)),
    'sfx_combat_swing_1': (lambda: sfx.swing(1), ('oneshot', SFX_CAP)),
    'sfx_combat_swing_2': (lambda: sfx.swing(2), ('oneshot', SFX_CAP)),
    'sfx_combat_swing_3': (lambda: sfx.swing(3), ('oneshot', SFX_CAP)),
    'sfx_combat_spell_fire': (lambda: sfx.spell('fire'), ('oneshot', SFX_CAP)),
    'sfx_combat_spell_ice': (lambda: sfx.spell('ice'), ('oneshot', SFX_CAP)),
    'sfx_combat_spell_dark': (lambda: sfx.spell('dark'), ('oneshot', SFX_CAP)),
    'sfx_combat_spell_arcane': (lambda: sfx.spell('arcane'), ('oneshot', SFX_CAP)),
    'sfx_combat_hit_1': (lambda: sfx.hit(1), ('oneshot', SFX_CAP)),
    'sfx_combat_hit_2': (lambda: sfx.hit(2), ('oneshot', SFX_CAP)),
    'sfx_combat_hit_3': (lambda: sfx.hit(3), ('oneshot', SFX_CAP)),
    'sfx_combat_miss': (lambda: sfx.miss(), ('oneshot', SFX_CAP)),
    'sfx_enemy_growl_1': (lambda: sfx.growl(1), ('oneshot', SFX_CAP)),
    'sfx_enemy_growl_2': (lambda: sfx.growl(2), ('oneshot', SFX_CAP)),
    'sfx_enemy_growl_3': (lambda: sfx.growl(3), ('oneshot', SFX_CAP)),
    'sfx_enemy_screech_1': (lambda: sfx.screech(1), ('oneshot', SFX_CAP)),
    'sfx_enemy_screech_2': (lambda: sfx.screech(2), ('oneshot', SFX_CAP)),
    'sfx_enemy_screech_3': (lambda: sfx.screech(3), ('oneshot', SFX_CAP)),
    'sfx_enemy_death_1': (lambda: sfx.death(1), ('oneshot', SFX_CAP)),
    'sfx_enemy_death_2': (lambda: sfx.death(2), ('oneshot', SFX_CAP)),
    'sfx_enemy_death_3': (lambda: sfx.death(3), ('oneshot', SFX_CAP)),
    'sfx_environment_torch_loop': (sfx.torch_loop, ('loop', -22.0)),
    'sfx_environment_ambience_loop': (sfx.ambience_loop, ('loop', -22.0)),
    'sfx_ui_move': (lambda: sfx.ui('move'), ('oneshot', UI_CAP)),
    'sfx_ui_click': (lambda: sfx.ui('click'), ('oneshot', UI_CAP)),
    'sfx_ui_confirm': (lambda: sfx.ui('confirm'), ('oneshot', UI_CAP)),
    'sfx_ui_cancel': (lambda: sfx.ui('cancel'), ('oneshot', UI_CAP)),
    'music_main_loop': (tracks.main_loop, ('loop', -15.0)),
    'music_battle_loop': (tracks.battle_loop, ('loop', -15.0)),
    'music_boss_loop': (tracks.boss_loop, ('loop', -15.0)),
    'music_victory_fanfare': (tracks.victory_fanfare, ('music', -15.0)),
    'music_ambient_crypt': (tracks.ambient_crypt, ('loop', -16.0)),
    'music_ambient_caverns': (tracks.ambient_caverns, ('loop', -16.0)),
    'music_ambient_depths': (tracks.ambient_depths, ('loop', -16.0)),
}


def is_loop(name):
    return JOBS[name][1][0] == 'loop'


# ---------------------------------------------------------------- finishing

def trim_oneshot(x):
    """Cut leading and trailing near-silence (below -55 dB of the peak), then
    fade 1 ms in and 15 ms out so nothing starts or stops on a click."""
    pk = dsp.peak(x)
    th = pk * 10 ** (-55.0 / 20)
    first = next(i for i, v in enumerate(x) if abs(v) > th)
    last = len(x) - next(i for i, v in enumerate(reversed(x)) if abs(v) > th)
    x = list(x[max(0, first - 8):min(len(x), last + dsp.ns(0.005))])
    dsp.fade_in(x, dsp.ns(0.001))
    dsp.fade_out(x, min(dsp.ns(0.015), len(x) // 6))
    return x


def pad_length(x, n):
    """Zero-pad to a multiple of 64 samples (Ogg stores the length rounded up to 64)
    that is not a multiple of 1024 (ffmpeg's decoder drops a block there)."""
    m = math.ceil(n / 64) * 64
    if m % 1024 == 0:
        m += 64
    return list(x) + [0.0] * (m - n)


def finish(name, sig):
    kind, target = JOBS[name][1]
    left, right = sig if isinstance(sig, tuple) else (sig, None)
    if kind == 'oneshot':
        left = trim_oneshot(left)
        g = PEAK / dsp.peak(left)
        mm = dsp.momentary_max([left, left]) + 20 * math.log10(g)
        if mm > target:
            g *= 10 ** ((target - mm) / 20)
        left = pad_length([v * g for v in left], len(left))
        return left, left
    if right is None:
        right = left
    lu = dsp.loudness([left, right])
    pk = max(dsp.peak(left), dsp.peak(right))
    g = min(10 ** ((target - lu) / 20), PEAK / pk)
    left = [v * g for v in left]
    right = [v * g for v in right]
    if kind == 'music':
        last = max(i for i, (a, b) in enumerate(zip(left, right)) if max(abs(a), abs(b)) > 1e-3)
        n = min(len(left), last + dsp.ns(0.03))
        left, right = left[:n], right[:n]
        for ch in (left, right):
            dsp.fade_out(ch, dsp.ns(0.3))
        return pad_length(left, n), pad_length(right, n)
    if len(left) % 64:
        raise ValueError(f'{name}: loop length {len(left)} is not a multiple of 64')
    # A loop can start anywhere and stay seamless. Start it on the quietest sample
    # in the 46 ms before the downbeat, so the very first play begins near zero.
    n = len(left)
    k = min(range(n - 2048, n + 1), key=lambda i: max(abs(left[i % n]), abs(right[i % n])))
    k %= n
    return left[k:] + left[:k], right[k:] + right[:k]


# ---------------------------------------------------------------- io

def to_pcm16(x):
    return array('h', (32767 if v >= 1.0 else -32768 if v <= -1.0 else int(round(v * 32767.0)) for v in x))


def write_wav(path, left, right):
    a, b = to_pcm16(left), to_pcm16(right)
    inter = array('h', bytes(4 * len(a)))
    inter[0::2] = a
    inter[1::2] = b
    if sys.byteorder == 'big':
        inter.byteswap()
    with wave.open(str(path), 'wb') as w:
        w.setnchannels(2)
        w.setsampwidth(2)
        w.setframerate(dsp.SR)
        w.writeframes(inter.tobytes())


def encode(wav, ogg):
    # The native Vorbis encoder: experimental, stereo only. bitexact keeps the
    # Ogg serial number and header fixed, so rebuilding gives identical files.
    subprocess.run([FFMPEG, '-nostdin', '-hide_banner', '-loglevel', 'error', '-y', '-i', str(wav),
                    '-ac', '2', '-c:a', 'vorbis', '-strict', '-2', '-q:a', '6', '-map_metadata', '-1',
                    '-fflags', '+bitexact', '-flags:a', '+bitexact', str(ogg)], check=True)


def build(name, levels=False):
    t0 = time.perf_counter()
    music.ANALYZE = levels
    res = JOBS[name][0]()
    song = None
    if isinstance(res, tuple) and len(res) == 3:
        left, right, song = res
        res = (left, right)
    left, right = finish(name, res)
    wav = WAV_DIR / f'{name}.wav'
    ogg = OUT_DIRS[name.split('_')[0]] / f'{name}.ogg'
    write_wav(wav, left, right)
    encode(wav, ogg)
    info = {
        'name': name,
        'secs': len(left) / dsp.SR,
        'peak': dsp.db(max(dsp.peak(left), dsp.peak(right))),
        'lufs': (dsp.loudness([left, right]) if JOBS[name][1][0] != 'oneshot'
                 else dsp.momentary_max([left, right])),
        'time': time.perf_counter() - t0,
        'levels': song.levels() if (song and levels) else None,
        'bpm': song.bpm if song else None,
    }
    return info


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--only', action='append', metavar='NAME',
                    help='build only this file (name, name.ogg or a glob); repeatable')
    ap.add_argument('--list', action='store_true', help='list the files this script builds')
    ap.add_argument('--levels', action='store_true', help='report per-part loudness for music')
    ap.add_argument('--jobs', type=int, default=os.cpu_count() or 4)
    args = ap.parse_args()
    if args.list:
        print('\n'.join(JOBS))
        return
    names = list(JOBS)
    if args.only:
        pats = [p[:-4] if p.endswith('.ogg') else p for p in args.only]
        names = [n for n in JOBS if any(fnmatch.fnmatchcase(n, p) for p in pats)]
        if not names:
            sys.exit(f'no file matches {args.only}; try --list')
    WAV_DIR.mkdir(parents=True, exist_ok=True)
    for d in OUT_DIRS.values():
        d.mkdir(parents=True, exist_ok=True)
    # slowest first so the pool finishes sooner
    names.sort(key=lambda n: (not n.startswith('music'), n))
    t0 = time.perf_counter()
    with ProcessPoolExecutor(max_workers=min(args.jobs, len(names))) as ex:
        results = list(ex.map(build, names, [args.levels] * len(names)))
    results.sort(key=lambda r: list(JOBS).index(r['name']))
    for r in results:
        lu = 'LUFS-M max' if JOBS[r['name']][1][0] == 'oneshot' else 'LUFS'
        bpm = f"  {r['bpm']:.2f} BPM" if r['bpm'] else ''
        print(f"{r['name']:32s} {r['secs']:6.2f} s  peak {r['peak']:5.1f} dBFS  {r['lufs']:6.1f} {lu}{bpm}")
        if r['levels']:
            print('    parts:', ', '.join(f'{k} {v}' for k, v in r['levels'].items()))
    print(f'built {len(results)} files in {time.perf_counter() - t0:.0f} s')


if __name__ == '__main__':
    main()
