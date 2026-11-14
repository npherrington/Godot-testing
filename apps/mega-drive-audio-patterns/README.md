# Mega Drive Audio Patterns

A browser app for designing two-operator FM sounds, the technique behind the Mega Drive's
sound chip, and saving them for the game. You play notes on the keyboard and drag the
parameters of the formula while you listen, with plots of what each one does.

```
y(t) = L · v · A(t) · sin(2π·f·t + I(t)·m(t))
m(t) = sin(2π·r·f·t + β·(m₋₁ + m₋₂)/2)
```

- **f** is the note's frequency and **t** the time since the key went down. Neither is a
  knob: f comes from the key you play.
- **The patch** is everything else:
  - **r**, the ratio of the modulator to the note
  - **β**, feedback of the modulator into itself
  - **L**, the level
  - **A(t)**, the volume envelope
  - **I(t)**, the index: how hard the modulator bends the carrier
- **Velocity v** comes from how hard you play; the keyboard sets it with a slider.

## Run it

[mise](https://mise.jdx.dev) pins Node and runs the tasks. Every task installs npm packages
first if `package-lock.json` changed.

```sh
cd apps/mega-drive-audio-patterns
mise install          # once: the pinned Node
mise run dev          # http://localhost:5173, hot reload
mise run start        # production build, served at http://localhost:4173
mise run build        # production build into dist/
mise run check        # typecheck, lint, tests, build: run before calling a change done
mise run fixtures     # after changing art/audio/fm.py: refresh the Python reference samples
mise tasks            # list them all
```

The plain npm scripts (`npm run dev`, `npm test`, ...) work too.

## Using it

- **Play** by clicking the keys or typing on the computer keyboard:
  - Z S X D C V G B H N J M play the lower octave.
  - Q 2 W 3 E R 5 T 6 Y 7 U I play the upper one.
  - `[` and `]` change the octave.
- **Drag a slider while holding a key** to hear the change live.
- **The plots** show the last key you played, held for the "hold time":
  - I(t) and A(t) over the whole note. Click or drag on either to move the cursor.
  - The waveform at the cursor, against a plain sine (I = 0).
  - The spectrum at the cursor. The FFT is measured from the samples. The dots are what the
    maths predicts: with no feedback, the formula is exactly Σₖ Jₖ(I)·sin(2π·(1 + k·r)·f·t),
    so there's a line at (1 + k·r)·f as loud as the Bessel function |Jₖ(I)|.
- **I(t) has five shapes:**
  - constant
  - decay: I₁ + (I₀ − I₁)·e^(−t/τ)
  - envelope: I₀·E(t), with its own attack, decay, sustain and release
  - wobble: I₀ + a·sin(2π·v·t)
  - formula: anything you type, using `t`, `f`, `pi`, `e`, `+ - * / ^`, `sin cos tan exp log sqrt
    abs floor min max`. It's parsed by a small expression parser, never by `eval`.
- **Times in the volume envelope:**
  - Attack is the rise time.
  - Decay and release are the times to fall 60 dB.
  - A note is silent (under one 16-bit step) 1.5 release times after the key goes up.

## Getting sounds into the game

- **Save to game** writes `art/audio/patches/<name>.json`. This needs `mise run dev` or
  `mise run start`, whose server has a small write endpoint (`vite-plugins/patch-library.ts`).
  From a plain static copy of `dist/`, the button downloads the JSON instead.
- **In music**, an FM patch is an instrument like any other in `art/audio/tracks.py`:

  ```python
  from fm import fm
  bass = Voice(s, fm, 'bass', patch='slap_bass', gain=0.5)
  ```

  Then rebuild with `python3 art/audio/build_audio.py`. The built-in presets work by name
  without saving.
- **As a sound effect**, use **WAV** in the app (16-bit mono, 44.1 kHz, the held note plus its
  release). Or render a note from Python:
  `python3 art/audio/fm.py slap_bass --note A2 --gate 0.4`.

## The app and the game make the same samples

- **One synth, three places.** `src/synth/voice.ts` renders the live keys (in an AudioWorklet),
  the plots and the WAV export. `art/audio/fm.py` repeats it line for line, with the arithmetic
  in the same order, for the game build.
- **The tests check it.** `src/synth/synth.test.ts` renders 30 notes and compares them with
  samples `fm.py` wrote (`src/synth/__fixtures__/python_reference.json`). The cases are every
  preset at two pitches, every index shape, feedback up to 2, and formulas that divide by zero
  or take logs of 0. At 16 bits they agree exactly.
- **If you change the maths, change both** files, then run `mise run fixtures` and
  `mise run test`.

## Files

| Path | What it is |
| --- | --- |
| `src/synth/patch.ts` | The patch format (`fm-patch/1`), the envelope and index functions, JSON checking |
| `src/synth/voice.ts` | `FmVoice`, one sounding note; `renderNote`; 16-bit conversion |
| `src/synth/expr.ts` | The formula language: tokenizer, parser, compiler to closures |
| `src/synth/spectrum.ts` | Bessel functions, the predicted sidebands, the FFT |
| `src/synth/presets/*.json` | Built-in patches (fm.py reads these too) |
| `src/audio/` | The AudioWorklet and the engine that drives it |
| `src/components/` | The UI: sliders, the I(t) editor, the keyboard, the plots |
| `src/components/ui/` | shadcn components (generated: add more with `npx shadcn@latest add <name>`) |
| `vite-plugins/patch-library.ts` | The dev server's patch endpoint |
| `../../art/audio/fm.py` | The Python twin, the `fm` instrument and a CLI |

The app sits in `apps/`, which has a `.gdignore`, so Godot never imports `node_modules`.
