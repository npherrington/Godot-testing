"""Two-operator FM voice: the Python twin of apps/mega-drive-audio-patterns.

    y(t) = level * velocity * A(t) * sin(2*pi*f*t + I(t) * m(t))
    m(t) = sin(2*pi*r*f*t + beta * (m[-1] + m[-2]) / 2)

A patch (JSON, format "fm-patch/1") sets the ratio r, feedback beta, level, the volume
envelope A(t) and the index I(t). Design patches in the app (`mise run dev` in
apps/mega-drive-audio-patterns), press Save, and they land in art/audio/patches/.

This file repeats the app's src/synth/patch.ts, voice.ts and expr.ts with the arithmetic
in the same order, so both render the same 16-bit samples (the app's tests compare them
against a fixture this file writes). Change one, change the other, then refresh the
fixture with `mise run fixtures`.

Use it in a track like any other instrument:

    from fm import fm
    bass = Voice(s, fm, 'bass', patch='slap_bass', gain=0.5)

Or render one note to a WAV (art/out/audio/ by default):

    python3 art/audio/fm.py slap_bass --note A2 --gate 0.4
    python3 art/audio/fm.py --list
"""

import argparse
import ast
import base64
import json
import math
import sys
import wave
from array import array
from functools import lru_cache
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent.parent
PATCHES = HERE / 'patches'
PRESETS = ROOT / 'apps' / 'mega-drive-audio-patterns' / 'src' / 'synth' / 'presets'
OUT = ROOT / 'art' / 'out' / 'audio'

SR = 44100
FORMAT = 'fm-patch/1'
TAU = 2.0 * math.pi
K60 = 6.907755278982138  # 3*ln(10): exp(-K60*x/T) falls 60 dB over x = T
TAIL_RELEASES = 1.505149978319906  # log10(32768)/3: release times until below one 16-bit step
INF = math.inf
NAN = math.nan


# ---------------------------------------------------------------- formulas
# The same language as the app's expr.ts: numbers, t, f, pi, e, + - * / ^ (or **),
# unary + -, brackets, sin cos tan exp log sqrt abs floor, and min/max of two or more.
# Python's maths functions raise where JavaScript's return Infinity or NaN, so these
# wrappers return what JavaScript would.

def _is_odd_int(x):
    return math.isfinite(x) and x == math.floor(x) and math.fmod(x, 2.0) != 0.0


def _div(a, b):
    try:
        return a / b
    except ZeroDivisionError:
        if a == 0 or math.isnan(a):
            return NAN
        return math.copysign(INF, a) * math.copysign(1.0, b)


def _pow(a, b):
    if math.isnan(b):
        return NAN
    if b == 0:
        return 1.0
    if math.isnan(a):
        return NAN
    if abs(a) == 1 and math.isinf(b):
        return NAN
    try:
        r = a ** b
    except ZeroDivisionError:  # 0 to a negative power
        return -INF if math.copysign(1.0, a) < 0 and _is_odd_int(b) else INF
    except OverflowError:
        return -INF if a < 0 and _is_odd_int(b) else INF
    return NAN if isinstance(r, complex) else r


def _finite_only(fn):
    def wrapped(x):
        return NAN if math.isinf(x) else fn(x)
    return wrapped


def _exp(x):
    try:
        return math.exp(x)
    except OverflowError:
        return INF


def _log(x):
    if math.isnan(x) or x < 0:
        return NAN
    return -INF if x == 0 else math.log(x)


def _sqrt(x):
    return NAN if x < 0 else math.sqrt(x)


def _floor(x):
    return float(math.floor(x)) if math.isfinite(x) else x


def _min(*xs):
    return NAN if any(math.isnan(x) for x in xs) else min(xs)


def _max(*xs):
    return NAN if any(math.isnan(x) for x in xs) else max(xs)


UNARY = {'sin': _finite_only(math.sin), 'cos': _finite_only(math.cos),
         'tan': _finite_only(math.tan), 'exp': _exp, 'log': _log, 'sqrt': _sqrt,
         'abs': abs, 'floor': _floor}
VARIADIC = {'min': _min, 'max': _max}
CONSTANTS = {'pi': math.pi, 'e': math.e}


class _Check(ast.NodeTransformer):
    """Allow only the formula language; turn / and ** into the JavaScript-like helpers."""

    def generic_visit(self, node):
        raise ValueError(f'not allowed in a formula: {type(node).__name__}')

    def visit_Expression(self, node):
        node.body = self.visit(node.body)
        return node

    def visit_BinOp(self, node):
        left, right = self.visit(node.left), self.visit(node.right)
        if isinstance(node.op, ast.Div):
            return ast.Call(ast.Name('_div', ast.Load()), [left, right], [])
        if isinstance(node.op, ast.Pow):
            return ast.Call(ast.Name('_pow', ast.Load()), [left, right], [])
        if not isinstance(node.op, (ast.Add, ast.Sub, ast.Mult)):
            raise ValueError(f'operator not allowed: {type(node.op).__name__}')
        node.left, node.right = left, right
        return node

    def visit_UnaryOp(self, node):
        if not isinstance(node.op, (ast.USub, ast.UAdd)):
            raise ValueError(f'operator not allowed: {type(node.op).__name__}')
        node.operand = self.visit(node.operand)
        return node

    def visit_Constant(self, node):
        if isinstance(node.value, bool) or not isinstance(node.value, (int, float)):
            raise ValueError(f'not a number: {node.value!r}')
        return ast.Constant(float(node.value))

    def visit_Name(self, node):
        if node.id in ('t', 'f'):
            return node
        if node.id in CONSTANTS:
            return ast.Constant(CONSTANTS[node.id])
        raise ValueError(f'unknown name {node.id!r} (use t, f, pi or e)')

    def visit_Call(self, node):
        name = node.func.id if isinstance(node.func, ast.Name) else None
        if node.keywords or any(isinstance(a, ast.Starred) for a in node.args):
            raise ValueError('functions take plain arguments')
        if name in UNARY:
            if len(node.args) != 1:
                raise ValueError(f'{name} takes one argument')
        elif name in VARIADIC:
            if len(node.args) < 2:
                raise ValueError(f'{name} takes two or more arguments')
        else:
            raise ValueError(f'unknown function {name!r}')
        args = [self.visit(a) for a in node.args]
        return ast.Call(ast.Name('_' + name, ast.Load()), args, [])


def compile_formula(text):
    """Formula text -> function of (t, f). Raises ValueError on anything outside the language."""
    src = text.replace('^', '**').replace('\n', ' ').replace('\t', ' ')
    try:
        tree = ast.parse(src, mode='eval')
    except SyntaxError as e:
        raise ValueError(f'formula does not parse: {text!r} ({e.msg})') from None
    body = _Check().visit(tree).body
    lam = ast.Expression(ast.Lambda(
        ast.arguments(posonlyargs=[], args=[ast.arg('t'), ast.arg('f')], kwonlyargs=[],
                      kw_defaults=[], defaults=[]), body))
    ast.fix_missing_locations(lam)
    env = {'__builtins__': {}, '_div': _div, '_pow': _pow}
    env.update({'_' + k: v for k, v in {**UNARY, **VARIADIC}.items()})
    return eval(compile(lam, '<formula>', 'eval'), env)  # noqa: S307 - the tree is checked above


# ---------------------------------------------------------------- patches

def _num(v, fallback, lo=-INF, hi=INF):
    if isinstance(v, bool) or not isinstance(v, (int, float)) or not math.isfinite(v):
        return float(fallback)
    return float(min(hi, max(lo, v)))


def _envelope(o, fb):
    return {'attack': _num(o.get('attack'), fb['attack'], 0, 10),
            'decay': _num(o.get('decay'), fb['decay'], 0, 30),
            'sustain': _num(o.get('sustain'), fb['sustain'], 0, 1),
            'release': _num(o.get('release'), fb['release'], 0, 10)}


DEFAULT_AMP = {'attack': 0.005, 'decay': 1.2, 'sustain': 0.6, 'release': 0.25}
DEFAULT_INDEX = {
    'constant': {'value': 2},
    'decay': {'start': 6, 'end': 1, 'tau': 0.12},
    'envelope': {'peak': 4, 'attack': 0.01, 'decay': 0.5, 'sustain': 0.4, 'release': 0.3},
    'wobble': {'center': 2, 'depth': 1.5, 'rate': 6},
}


def read_patch(raw):
    """Check and clean a patch dict exactly as the app's readPatch does."""
    if not isinstance(raw, dict):
        raise ValueError('a patch is a JSON object')
    if raw.get('format') != FORMAT:
        raise ValueError(f'format must be "{FORMAT}"')
    ix = raw.get('index') or {}
    shape = ix.get('shape')
    if shape == 'constant':
        index = {'shape': shape, 'value': _num(ix.get('value'), 2)}
    elif shape == 'decay':
        d = DEFAULT_INDEX['decay']
        index = {'shape': shape, 'start': _num(ix.get('start'), d['start']),
                 'end': _num(ix.get('end'), d['end']), 'tau': _num(ix.get('tau'), d['tau'], 0)}
    elif shape == 'envelope':
        d = DEFAULT_INDEX['envelope']
        index = {'shape': shape, 'peak': _num(ix.get('peak'), d['peak']), **_envelope(ix, d)}
    elif shape == 'wobble':
        d = DEFAULT_INDEX['wobble']
        index = {'shape': shape, 'center': _num(ix.get('center'), d['center']),
                 'depth': _num(ix.get('depth'), d['depth']),
                 'rate': _num(ix.get('rate'), d['rate'], 0)}
    elif shape == 'formula':
        if not isinstance(ix.get('expr'), str):
            raise ValueError('index.expr must be a string')
        compile_formula(ix['expr'])
        index = {'shape': shape, 'expr': ix['expr']}
    else:
        raise ValueError(f'unknown index shape {shape!r}')
    name = raw.get('name')
    return {'format': FORMAT, 'name': name if isinstance(name, str) and name else 'untitled',
            'ratio': _num(raw.get('ratio'), 1, 0.0625, 32),
            'feedback': _num(raw.get('feedback'), 0, 0, 2),
            'level': _num(raw.get('level'), 0.8, 0, 1),
            'amp': _envelope(raw.get('amp') or {}, DEFAULT_AMP),
            'index': index}


def patch_names():
    """Saved patches (art/audio/patches/) first, then the app's built-in presets."""
    names = {}
    for folder in (PRESETS, PATCHES):
        for p in sorted(folder.glob('*.json')):
            names[p.stem] = p
    return names


@lru_cache(maxsize=None)
def _load(path):
    return read_patch(json.loads(Path(path).read_text()))


def load_patch(name):
    """A patch by name (art/audio/patches/<name>.json, else a built-in preset) or by path."""
    if name.endswith('.json'):
        return _load(str(Path(name).resolve()))
    path = patch_names().get(name)
    if path is None:
        raise KeyError(f'no patch named {name!r}; have: {", ".join(sorted(patch_names()))}')
    return _load(str(path))


# ---------------------------------------------------------------- the voice

def ads(t, e):
    if t < e['attack']:
        return t / e['attack']
    if e['decay'] <= 0:
        return e['sustain']
    return e['sustain'] + (1 - e['sustain']) * math.exp((-K60 * (t - e['attack'])) / e['decay'])


def envelope(t, e, g):
    """g is when the key was released (inf while held)."""
    if t < g:
        return ads(t, e)
    if e['release'] <= 0:
        return 0.0
    return ads(g, e) * math.exp((-K60 * (t - g)) / e['release'])


def index_fn(spec):
    shape = spec['shape']
    if shape == 'constant':
        v = spec['value']
        return lambda t, f, g: v
    if shape == 'decay':
        start, end, tau = spec['start'], spec['end'], spec['tau']
        if tau <= 0:
            return lambda t, f, g: end
        return lambda t, f, g: end + (start - end) * math.exp(-t / tau)
    if shape == 'envelope':
        peak = spec['peak']
        return lambda t, f, g: peak * envelope(t, spec, g)
    if shape == 'wobble':
        center, depth, rate = spec['center'], spec['depth'], spec['rate']
        return lambda t, f, g: center + depth * math.sin(TAU * rate * t)
    fn = compile_formula(spec['expr'])

    def formula(t, f, g):
        v = fn(t, f)
        return v if math.isfinite(v) else 0.0
    return formula


def tail_seconds(p):
    return p['amp']['release'] * TAIL_RELEASES


def render(patch, freq, gate_n, vel=1.0, sr=SR, limit=None):
    """One note held for gate_n samples then released, to the end of its release.
    Same samples as the app's renderNote (voice.ts)."""
    ratio, beta, env = patch['ratio'], patch['feedback'], patch['amp']
    amp = patch['level'] * vel
    index = index_fn(patch['index'])
    total = gate_n + math.ceil(tail_seconds(patch) * sr)
    if limit is not None:
        total = min(total, limit)
    g_released = gate_n / sr
    out = [0.0] * total
    m1 = m2 = 0.0
    sin = math.sin
    f = freq
    for n in range(total):
        t = n / sr
        g = INF if n < gate_n else g_released
        i = index(t, f, g)
        m = sin(TAU * ratio * f * t + beta * (m1 + m2) * 0.5)
        m2 = m1
        m1 = m
        out[n] = amp * envelope(t, env, g) * sin(TAU * f * t + i * m)
    return out


def hz(midi):
    return 440.0 * 2.0 ** ((midi - 69) / 12.0)


def fm(midi, gate, vel, rng, patch='electric_piano'):
    """Instrument for music.Voice: an FM patch made in apps/mega-drive-audio-patterns.
    gate is in samples, like the other instruments; rng is unused (FM is deterministic)."""
    return render(load_patch(patch), hz(midi), gate, vel)


def to_int16(x):
    """Clip to +-1, scale by 32767, round half up (the app's toInt16)."""
    return array('h', (math.floor(max(-1.0, min(1.0, v)) * 32767 + 0.5) for v in x))


def write_wav(path, samples, sr=SR):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    pcm = to_int16(samples)
    if sys.byteorder == 'big':
        pcm.byteswap()
    with wave.open(str(path), 'wb') as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(sr)
        w.writeframes(pcm.tobytes())
    return path


# ---------------------------------------------------------------- reference fixture

FIXTURE_LEN = 2048
FIXTURE_GATE = 1200

# Cases beyond the presets: every index shape, envelope edge cases, feedback, and
# formulas that hit the JavaScript-vs-Python edge semantics (division by zero, log 0,
# negative square roots, powers).
EXTRA = [
    ('feedback 0.5', {'ratio': 1, 'feedback': 0.5, 'index': {'shape': 'constant', 'value': 1}}),
    ('feedback 1.0', {'ratio': 1, 'feedback': 1.0, 'index': {'shape': 'constant', 'value': 1.5}}),
    ('feedback 2.0', {'ratio': 1, 'feedback': 2.0, 'index': {'shape': 'constant', 'value': 2}}),
    ('ratio 0.5', {'ratio': 0.5, 'index': {'shape': 'decay', 'start': 3, 'end': 1, 'tau': 0.01}}),
    ('decay tau 0', {'ratio': 3, 'index': {'shape': 'decay', 'start': 3, 'end': 2, 'tau': 0}}),
    ('envelope index', {'ratio': 2, 'index': {'shape': 'envelope', 'peak': 5, 'attack': 0.005,
                                              'decay': 0.01, 'sustain': 0.2, 'release': 0.01}}),
    ('wobble', {'ratio': 1.5, 'index': {'shape': 'wobble', 'center': 2, 'depth': 2, 'rate': 90}}),
    ('no attack, no release', {'amp': {'attack': 0, 'decay': 0, 'sustain': 0.7, 'release': 0}}),
    ('formula 1/t', {'index': {'shape': 'formula', 'expr': 'min(1/t, 8)'}}),
    ('formula log', {'index': {'shape': 'formula', 'expr': '-log(t)/4 + sqrt(-1)'}}),
    ('formula powers', {'index': {'shape': 'formula', 'expr': '-t^2*1000 + 2^-t*3 + (t*200)**0.5'}}),
    ('formula f and floor', {'index': {'shape': 'formula',
                                       'expr': 'f/100*exp(-80*t) + floor(t*400)/4 + max(0, 1-90*t, 0.2)'}}),
]


def fixture():
    base = {'format': FORMAT, 'name': 'case', 'ratio': 1, 'feedback': 0, 'level': 0.8,
            'amp': {'attack': 0.002, 'decay': 0.05, 'sustain': 0.5, 'release': 0.01},
            'index': {'shape': 'constant', 'value': 2}}
    cases = []
    for path in sorted(PRESETS.glob('*.json')):
        raw = json.loads(path.read_text())
        for freq, vel in ((110.0, 1.0), (523.2511306011972, 0.7)):
            cases.append((f'preset {path.stem} at {freq:g} Hz', raw, freq, vel))
    for label, over in EXTRA:
        cases.append((label, {**base, **over}, 220.0, 1.0))
    out = []
    for label, raw, freq, vel in cases:
        patch = read_patch(raw)
        pcm = to_int16(render(patch, freq, FIXTURE_GATE, vel, SR, FIXTURE_LEN))
        if sys.byteorder == 'big':
            pcm.byteswap()
        out.append({'label': label, 'patch': raw, 'freq': freq, 'velocity': vel,
                    'gateN': FIXTURE_GATE, 'limit': FIXTURE_LEN, 'sr': SR,
                    'int16le': base64.b64encode(pcm.tobytes()).decode()})
    return {'generator': 'art/audio/fm.py --fixture', 'cases': out}


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('patch', nargs='?', help='patch name or .json path')
    ap.add_argument('--note', default='A3', help='note name like A3 or C#5 (default A3)')
    ap.add_argument('--gate', type=float, default=0.5, help='seconds the key is held (default 0.5)')
    ap.add_argument('--vel', type=float, default=1.0, help='velocity 0-1 (default 1)')
    ap.add_argument('--out', help='WAV path (default art/out/audio/fm_<patch>_<note>.wav)')
    ap.add_argument('--list', action='store_true', help='list patch names')
    ap.add_argument('--fixture', metavar='PATH', help="write the app tests' reference samples")
    args = ap.parse_args()
    if args.list:
        for name, path in patch_names().items():
            print(f'{name:20} {path.relative_to(ROOT)}')
        return
    if args.fixture:
        Path(args.fixture).write_text(json.dumps(fixture(), indent=1) + '\n')
        print(f'wrote {args.fixture}')
        return
    if not args.patch:
        ap.error('give a patch name, --list or --fixture')
    from dsp import note  # only the CLI needs note names
    patch = load_patch(args.patch)
    sig = render(patch, hz(note(args.note)), round(args.gate * SR), args.vel)
    out = args.out or OUT / f'fm_{Path(args.patch).stem}_{args.note.replace("#", "s")}.wav'
    print(f'wrote {write_wav(out, sig)} ({len(sig) / SR:.2f} s)')


if __name__ == '__main__':
    main()
