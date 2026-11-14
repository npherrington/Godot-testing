#!/usr/bin/env python3
"""Measure every built sound, since nobody can listen in a build.

    python3 art/audio/verify_audio.py            # all files
    python3 art/audio/verify_audio.py --only 'music_*'

Per file: ffprobe codec, channels, rate and duration of the .ogg; the Ogg end
granule (the length a decoder will play) against the WAV length; peak, RMS and
loudness of the WAV; leading and trailing silence (below -60 dBFS); clipped
samples; and for loops, the jump from the last sample back to the first, before
and after Vorbis encoding, next to the largest normal sample-to-sample step.
Exits 1 if anything fails a check.
"""

import sys

sys.dont_write_bytecode = True

import argparse
import fnmatch
import json
import math
import shutil
import struct
import subprocess
import wave
from array import array
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import dsp  # noqa: E402
from build_audio import FFMPEG, JOBS, OUT_DIRS, WAV_DIR, is_loop  # noqa: E402

FFPROBE = shutil.which('ffprobe') or '/opt/homebrew/bin/ffprobe'
SILENCE = 10 ** (-60 / 20)


def ffprobe(path):
    out = subprocess.run([FFPROBE, '-v', 'error', '-show_entries',
                          'stream=codec_name,channels,sample_rate,duration', '-of', 'json', str(path)],
                         capture_output=True, text=True, check=True).stdout
    s = json.loads(out)['streams'][0]
    return s['codec_name'], int(s['channels']), int(s['sample_rate']), float(s['duration'])


def end_granule(path):
    """Granule position of the last Ogg page = total samples a decoder outputs."""
    d = Path(path).read_bytes()
    i = last = 0
    while (i := d.find(b'OggS', i)) >= 0:
        last = struct.unpack('<q', d[i + 6:i + 14])[0]
        nseg = d[i + 26]
        i += 27 + nseg + sum(d[i + 27:i + 27 + nseg])
    return last


def split(pcm):
    a = array('h')
    a.frombytes(pcm)
    if sys.byteorder == 'big':
        a.byteswap()
    return [v / 32768.0 for v in a[0::2]], [v / 32768.0 for v in a[1::2]], a


def read_wav(path):
    with wave.open(str(path)) as w:
        assert w.getnchannels() == 2 and w.getsampwidth() == 2 and w.getframerate() == dsp.SR
        return split(w.readframes(w.getnframes()))


def decode(path):
    pcm = subprocess.run([FFMPEG, '-v', 'error', '-i', str(path), '-f', 's16le', '-ac', '2', '-'],
                         capture_output=True, check=True).stdout
    return split(pcm)


def silence_ms(x):
    lead = next((i for i, v in enumerate(x) if abs(v) > SILENCE), len(x))
    trail = next((i for i, v in enumerate(reversed(x)) if abs(v) > SILENCE), len(x))
    return 1000.0 * lead / dsp.SR, 1000.0 * trail / dsp.SR


def seam(L, R):
    """(jump across the loop point, 99.99th percentile step inside the file)."""
    jump = max(abs(L[0] - L[-1]), abs(R[0] - R[-1]))
    steps = sorted(abs(x[i] - x[i - 1]) for x in (L, R) for i in range(1, len(x)))
    return jump, steps[int(0.9999 * (len(steps) - 1))]


def check(name):
    ogg = OUT_DIRS[name.split('_')[0]] / f'{name}.ogg'
    wav = WAV_DIR / f'{name}.wav'
    codec, ch, sr, dur = ffprobe(ogg)
    L, R, raw = read_wav(wav)
    n = len(L)
    kind = JOBS[name][1][0]
    loop = is_loop(name)
    pk = max(dsp.peak(L), dsp.peak(R))
    r = {
        'name': name, 'codec': codec, 'ch': ch, 'sr': sr, 'dur': dur, 'n': n,
        'granule': end_granule(ogg), 'peak': dsp.db(pk),
        'rms': dsp.db(math.sqrt((sum(v * v for v in L) + sum(v * v for v in R)) / (2 * n))),
        'lufs': dsp.loudness([L, R]) if kind != 'oneshot' else dsp.momentary_max([L, R]),
        'clipped': sum(1 for v in raw if v >= 32767 or v <= -32768),
        'loop': loop,
    }
    sl = silence_ms([max(abs(a), abs(b)) for a, b in zip(L, R)])
    r['lead_ms'], r['trail_ms'] = sl
    dl, dr, _ = decode(ogg)
    r['dec_peak'] = dsp.db(max(dsp.peak(dl), dsp.peak(dr)))
    if loop:
        r['seam'], r['step'] = seam(L, R)
        m = min(n, len(dl))
        r['dec_seam'], r['dec_step'] = seam(dl[:m], dr[:m])
        r['start'] = max(abs(L[0]), abs(R[0]))
    problems = []
    if codec != 'vorbis' or ch != 2 or sr != dsp.SR:
        problems.append('format')
    if r['granule'] != n:
        problems.append(f"length {r['granule']} != {n}")
    if r['clipped'] or r['peak'] > -0.9 or r['dec_peak'] > -0.1:
        problems.append('clipping or over -1 dBFS')
    if r['lufs'] < -30:
        problems.append('near silent')
    if loop and (r['seam'] > r['step'] or r['dec_seam'] > 2 * r['dec_step']):
        problems.append('loop seam jump')
    if not loop and (r['lead_ms'] > 5 or (kind == 'oneshot' and r['trail_ms'] > 60)):
        problems.append('silence at an end')
    r['problems'] = problems
    return r


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--only', action='append', metavar='GLOB')
    args = ap.parse_args()
    names = [n for n in JOBS if not args.only or any(fnmatch.fnmatchcase(n, p) for p in args.only)]
    from concurrent.futures import ProcessPoolExecutor
    with ProcessPoolExecutor() as ex:
        rows = list(ex.map(check, names))
    print(f"{'file':32s} {'ogg s':>6s} ch    Hz {'peak':>5s} {'dec':>5s} {'rms':>6s} {'loud':>6s} "
          f"{'lead':>5s} {'trail':>5s}  loop seam (wav / ogg vs max step)")
    bad = 0
    for r in rows:
        line = (f"{r['name']:32s} {r['dur']:6.2f} {r['ch']:2d} {r['sr']:5d} {r['peak']:5.1f} {r['dec_peak']:5.1f} "
                f"{r['rms']:6.1f} {r['lufs']:6.1f} {r['lead_ms']:5.1f} {r['trail_ms']:5.1f}")
        if r['loop']:
            line += (f"  {r['seam']:.4f}/{r['step']:.4f}  {r['dec_seam']:.4f}/{r['dec_step']:.4f}"
                     f"  start {dsp.db(r['start']):.0f} dB")
        if r['problems']:
            bad += 1
            line += '  <-- ' + '; '.join(r['problems'])
        print(line)
    print('loudness: integrated LUFS for loops and music, loudest 400 ms (LUFS-M) for one-shots')
    print(f"{len(rows)} files, {bad} with problems; every Ogg end granule matches its WAV length"
          if not any('length' in p for r in rows for p in r['problems']) else f'{bad} with problems')
    sys.exit(1 if bad else 0)


if __name__ == '__main__':
    main()
