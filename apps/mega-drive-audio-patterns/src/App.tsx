import { useCallback, useDeferredValue, useEffect, useMemo, useState } from 'react'
import {
  DownloadSimpleIcon,
  FloppyDiskIcon,
  FolderOpenIcon,
  MoonIcon,
  PlayIcon,
  SunIcon,
  WaveformIcon,
} from '@phosphor-icons/react'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import {
  Select,
  SelectContent,
  SelectGroup,
  SelectItem,
  SelectLabel,
  SelectSeparator,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select'
import { Switch } from '@/components/ui/switch'
import { Equation } from '@/components/Equation'
import { EnvelopeSliders, IndexEditor } from '@/components/IndexEditor'
import { Keyboard } from '@/components/Keyboard'
import { ParamSlider } from '@/components/ParamSlider'
import { SpectrumPlot } from '@/components/plots/SpectrumPlot'
import { TimePlot } from '@/components/plots/TimePlot'
import { WavePlot } from '@/components/plots/WavePlot'
import * as engine from '@/audio/engine'
import { download, listSaved, loadDraft, openJson, saveDraft, saveToRepo } from '@/lib/files'
import { DEFAULT_INDEX, readPatch, slug, type IndexShape, type IndexSpec, type Patch } from '@/synth/patch'
import { PRESETS, titleOf } from '@/synth/presets'
import { midiToHz, noteName, renderNote, toInt16 } from '@/synth/voice'
import { wavBytes } from '@/synth/wav'

const SR = 44100
/** The plots show at most this much of a note. */
const PLOT_SECONDS = 6

type Stash = { [S in IndexShape]: Extract<IndexSpec, { shape: S }> }
const stashFor = (spec: IndexSpec): Stash => ({ ...DEFAULT_INDEX, [spec.shape]: spec })

/** Ratios snap to quarters below 1, halves below 4, whole numbers above. */
function snapRatio(v: number): number {
  if (v < 1) return Math.max(0.25, Math.round(v * 4) / 4)
  if (v < 4) return Math.round(v * 2) / 2
  return Math.round(v)
}

/** What the ratio does to the spectrum, from its simplest fraction p/q. */
function ratioKind(r: number): { label: string; detail: string } {
  for (let q = 1; q <= 8; q++) {
    const p = Math.round(r * q)
    if (p > 0 && Math.abs(p / q - r) < 1e-6) {
      if (q === 1)
        return {
          label: 'harmonic',
          detail:
            p === 1
              ? 'r = 1: lines on every harmonic, brassy or saw-like'
              : p % 2 === 0
                ? `r = ${p}: even r skips harmonics (r = 2 leaves odd ones only: hollow, reed-like)`
                : `r = ${p}: lines on harmonics, spaced ${p} apart`,
        }
      return { label: `${p}:${q}`, detail: `lines on multiples of f/${q}: the pitch sounds ${q === 2 ? 'an octave' : 'further'} lower` }
    }
  }
  return { label: 'inharmonic', detail: 'lines fall between harmonics: bells, metal, noise' }
}

function useTheme(): [boolean, () => void] {
  const [dark, setDark] = useState(() => document.documentElement.classList.contains('dark'))
  const toggle = () => {
    const next = !dark
    document.documentElement.classList.toggle('dark', next)
    try {
      localStorage.setItem('theme', next ? 'dark' : 'light')
    } catch {
      // not remembered; fine
    }
    setDark(next)
  }
  return [dark, toggle]
}

export default function App() {
  const [patch, setPatch] = useState<Patch>(() => loadDraft() ?? PRESETS[0])
  const [stash, setStash] = useState<Stash>(() => stashFor(patch.index))
  const [loadId, setLoadId] = useState(0)
  const [snap, setSnap] = useState(true)
  const [midi, setMidi] = useState(57)
  const [gate, setGate] = useState(0.6)
  const [velocity, setVelocity] = useState(1)
  const [cursor, setCursor] = useState(0.02)
  const [octave, setOctave] = useState(3)
  const [held, setHeld] = useState<Set<number>>(new Set())
  const [saved, setSaved] = useState<Patch[] | null>(null)
  const [status, setStatus] = useState<string | null>(null)
  const [dark, toggleTheme] = useTheme()

  // ---- patch state
  const update = useCallback((changes: Partial<Patch>) => setPatch((p) => ({ ...p, ...changes })), [])
  const setIndex = (index: IndexSpec) => {
    setStash((s) => ({ ...s, [index.shape]: index }))
    update({ index })
  }
  const load = (p: Patch) => {
    setPatch(p)
    setStash(stashFor(p.index))
    setLoadId((n) => n + 1)
  }

  useEffect(() => {
    engine.setPatch(patch)
    saveDraft(patch)
  }, [patch])

  useEffect(() => {
    void listSaved().then(setSaved)
  }, [])

  useEffect(() => {
    if (!status) return
    const id = setTimeout(() => setStatus(null), 8000)
    return () => clearTimeout(id)
  }, [status])

  // ---- the rendered note behind the plots
  const freq = midiToHz(midi)
  const shown = useDeferredValue(patch)
  const render = useMemo(
    () => renderNote(shown, freq, Math.round(gate * SR), velocity, SR, PLOT_SECONDS * SR),
    [shown, freq, gate, velocity],
  )
  const duration = render.samples.length / SR
  const t = Math.min(cursor, duration - 1 / SR)
  const at = Math.max(0, Math.floor(t * SR))
  const indexNow = render.index[at] ?? 0
  const volumeNow = render.volume[at] ?? 0

  // ---- playing
  const noteOn = (m: number) => {
    setMidi(m)
    setHeld((h) => new Set(h).add(m))
    void engine.noteOn(String(m), midiToHz(m), velocity)
  }
  const noteOff = (m: number) => {
    setHeld((h) => {
      const next = new Set(h)
      next.delete(m)
      return next
    })
    engine.noteOff(String(m))
  }
  const playRendered = () => {
    const full = renderNote(patch, freq, Math.round(gate * SR), velocity, SR)
    void engine.playSamples(full.samples, SR)
  }

  // ---- files
  const name = slug(patch.name)
  const save = async () => {
    const file = await saveToRepo({ ...patch, name })
    if (file) {
      setStatus(`Saved ${file}. In a track: Voice(s, fm, 'part', patch='${name}')`)
      setSaved(await listSaved())
    } else {
      download(`${name}.json`, JSON.stringify({ ...patch, name }, null, 2) + '\n', 'application/json')
      setStatus(`No dev server to save through, so it downloaded. Put ${name}.json in art/audio/patches/.`)
    }
  }
  const open = async () => {
    try {
      load(readPatch(await openJson()))
      setStatus('Opened.')
    } catch (e) {
      setStatus(`Couldn't open that file: ${e instanceof Error ? e.message : String(e)}`)
    }
  }
  const exportWav = () => {
    const full = renderNote(patch, freq, Math.round(gate * SR), velocity, SR)
    const note = noteName(midi).replace('#', 's')
    download(`fm_${name}_${note}.wav`, wavBytes(toInt16(full.samples), SR), 'audio/wav')
    setStatus(`Exported fm_${name}_${note}.wav: 16-bit mono, 44.1 kHz, ${(full.samples.length / SR).toFixed(2)} s.`)
  }

  const kind = ratioKind(patch.ratio)
  const presetValue = PRESETS.some((p) => p.name === patch.name)
    ? `preset:${patch.name}`
    : saved?.some((p) => p.name === patch.name)
      ? `saved:${patch.name}`
      : undefined

  return (
    <div className="min-h-svh bg-background">
      <header className="flex flex-wrap items-center gap-x-4 gap-y-3 border-b px-4 py-3">
        <div className="flex items-center gap-2">
          <WaveformIcon className="size-5 text-[var(--series-1)]" weight="bold" />
          <div>
            <h1 className="text-sm font-semibold">Mega Drive Audio Patterns</h1>
            <p className="text-[11px] text-muted-foreground">Two-operator FM patch designer</p>
          </div>
        </div>
        <div className="ml-auto flex flex-wrap items-center gap-2">
          <Select
            value={presetValue ?? ''}
            onValueChange={(v) => {
              const [kindOf, n] = v.split(':')
              const list = kindOf === 'preset' ? PRESETS : (saved ?? [])
              const found = list.find((p) => p.name === n)
              if (found) load(found)
            }}
          >
            <SelectTrigger size="sm" className="w-44" aria-label="Load a patch">
              <SelectValue placeholder="Load a patch…" />
            </SelectTrigger>
            <SelectContent>
              <SelectGroup>
                <SelectLabel>Presets</SelectLabel>
                {PRESETS.map((p) => (
                  <SelectItem key={p.name} value={`preset:${p.name}`}>
                    {titleOf(p.name)}
                  </SelectItem>
                ))}
              </SelectGroup>
              {saved && saved.length > 0 && (
                <>
                  <SelectSeparator />
                  <SelectGroup>
                    <SelectLabel>Saved in art/audio/patches</SelectLabel>
                    {saved.map((p) => (
                      <SelectItem key={p.name} value={`saved:${p.name}`}>
                        {p.name}
                      </SelectItem>
                    ))}
                  </SelectGroup>
                </>
              )}
            </SelectContent>
          </Select>
          <Input
            value={patch.name}
            onChange={(e) => update({ name: e.target.value })}
            onBlur={() => update({ name })}
            className="h-7 w-40 text-xs"
            aria-label="Patch name"
            spellCheck={false}
          />
          <Button size="sm" onClick={save} title="Write art/audio/patches/<name>.json (downloads it without the dev server)">
            <FloppyDiskIcon data-icon="inline-start" />
            Save to game
          </Button>
          <Button size="sm" variant="outline" onClick={open}>
            <FolderOpenIcon data-icon="inline-start" />
            Open
          </Button>
          <Button
            size="sm"
            variant="outline"
            onClick={() => download(`${name}.json`, JSON.stringify({ ...patch, name }, null, 2) + '\n', 'application/json')}
          >
            <DownloadSimpleIcon data-icon="inline-start" />
            JSON
          </Button>
          <Button size="sm" variant="outline" onClick={exportWav}>
            <DownloadSimpleIcon data-icon="inline-start" />
            WAV
          </Button>
          <Button size="icon-sm" variant="ghost" onClick={toggleTheme} aria-label={dark ? 'Light theme' : 'Dark theme'}>
            {dark ? <SunIcon /> : <MoonIcon />}
          </Button>
        </div>
        {status && (
          <p className="basis-full text-[11px] text-muted-foreground" role="status">
            {status}
          </p>
        )}
      </header>

      <Equation patch={patch} freq={freq} velocity={velocity} cursor={t} index={indexNow} volume={volumeNow} />

      <main className="grid gap-4 p-4 lg:grid-cols-[minmax(300px,380px)_minmax(0,1fr)]">
        <aside className="flex flex-col gap-4">
          <Card size="sm">
            <CardHeader>
              <CardTitle>Operators</CardTitle>
              <CardDescription>The modulator runs at r times the note and bends the carrier's phase.</CardDescription>
            </CardHeader>
            <CardContent className="flex flex-col gap-4">
              <ParamSlider
                symbol="r"
                label="ratio, modulator ÷ note"
                log
                min={0.125}
                max={32}
                digits={3}
                snap={snap ? snapRatio : undefined}
                value={patch.ratio}
                onChange={(ratio) => update({ ratio })}
              />
              <div className="flex items-center justify-between gap-2">
                <div className="flex items-center gap-2">
                  <Switch id="snap" size="sm" checked={snap} onCheckedChange={setSnap} />
                  <Label htmlFor="snap" className="text-[11px] font-normal text-muted-foreground">
                    Snap to simple ratios
                  </Label>
                </div>
                <Badge variant="secondary" title={kind.detail}>
                  {kind.label}
                </Badge>
              </div>
              <p className="-mt-2 text-[11px] text-muted-foreground">{kind.detail}</p>
              <ParamSlider
                symbol="β"
                label="feedback, modulator into itself"
                min={0}
                max={2}
                value={patch.feedback}
                onChange={(feedback) => update({ feedback })}
                hint="0 is pure FM. Around 1 the modulator becomes saw-like; near 2 it turns to noise."
              />
              <ParamSlider symbol="L" label="level" min={0} max={1} value={patch.level} onChange={(level) => update({ level })} />
            </CardContent>
          </Card>

          <Card size="sm">
            <CardHeader>
              <CardTitle>
                Index <span className="text-[var(--series-3)]">I(t)</span>
              </CardTitle>
              <CardDescription>How hard the modulator bends the carrier. 0 is a pure sine; more is brighter.</CardDescription>
            </CardHeader>
            <CardContent>
              <IndexEditor key={loadId} spec={patch.index} stash={stash} onChange={setIndex} />
            </CardContent>
          </Card>

          <Card size="sm">
            <CardHeader>
              <CardTitle>
                Volume <span className="text-[var(--series-1)]">A(t)</span>
              </CardTitle>
              <CardDescription>
                Rises over a, falls 60 dB toward s over d, then 60 dB over R after the key goes up.
              </CardDescription>
            </CardHeader>
            <CardContent className="flex flex-col gap-4">
              <EnvelopeSliders value={patch.amp} onChange={(amp) => update({ amp })} />
            </CardContent>
          </Card>
        </aside>

        <section className="flex min-w-0 flex-col gap-4">
          <Card size="sm">
            <CardHeader>
              <CardTitle>Play</CardTitle>
              <CardDescription>
                Keys play live, and sliders change a held note as you drag. The plots show the last key: {noteName(midi)},{' '}
                {freq.toFixed(1)} Hz, held {gate.toFixed(2)} s.
              </CardDescription>
            </CardHeader>
            <CardContent className="flex flex-col gap-4">
              <Keyboard octave={octave} onOctave={setOctave} held={held} selected={midi} onNoteOn={noteOn} onNoteOff={noteOff} />
              <div className="grid gap-4 sm:grid-cols-[1fr_1fr_auto] sm:items-end">
                <ParamSlider symbol="v" label="velocity" min={0.05} max={1} value={velocity} onChange={setVelocity} />
                <ParamSlider
                  symbol="g"
                  label="hold time for plots and WAV"
                  log
                  min={0.02}
                  max={4}
                  unit="s"
                  value={gate}
                  onChange={setGate}
                />
                <Button variant="secondary" onClick={playRendered}>
                  <PlayIcon data-icon="inline-start" weight="fill" />
                  Play {noteName(midi)} for {gate.toFixed(2)} s
                </Button>
              </div>
            </CardContent>
          </Card>

          <Card size="sm">
            <CardHeader>
              <CardTitle>Over the note</CardTitle>
              <CardDescription>Click or drag on a plot to move the cursor; the waveform and spectrum show that moment.</CardDescription>
            </CardHeader>
            <CardContent className="grid gap-6 xl:grid-cols-2">
              <TimePlot
                title={<span className="text-[var(--series-3)]">Index I(t)</span>}
                values={render.index}
                sr={SR}
                gateN={render.gateN}
                cursor={t}
                onCursor={setCursor}
                color="series3"
                symbol="I"
              />
              <TimePlot
                title={<span className="text-[var(--series-1)]">Volume A(t)</span>}
                values={render.volume}
                sr={SR}
                gateN={render.gateN}
                cursor={t}
                onCursor={setCursor}
                color="series1"
                symbol="A"
                range={[0, 1.05]}
              />
            </CardContent>
          </Card>

          <Card size="sm">
            <CardContent className="grid gap-6 xl:grid-cols-2">
              <WavePlot samples={render.samples} volume={render.volume} gain={shown.level * velocity} sr={SR} freq={freq} cursor={t} />
              <SpectrumPlot
                samples={render.samples}
                sr={SR}
                freq={freq}
                cursor={t}
                index={indexNow}
                ratio={shown.ratio}
                feedback={shown.feedback}
                gain={shown.level * velocity * volumeNow}
              />
            </CardContent>
          </Card>
        </section>
      </main>
    </div>
  )
}
