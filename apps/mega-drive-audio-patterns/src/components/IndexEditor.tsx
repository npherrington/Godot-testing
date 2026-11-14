// Choose the shape of I(t), the modulation index over time, and set its parameters,
// or type a formula of your own.

import { useState } from 'react'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { ToggleGroup, ToggleGroupItem } from '@/components/ui/toggle-group'
import { ParamSlider } from './ParamSlider'
import { FUNCTIONS, tryCompile } from '@/synth/expr'
import { INDEX_SHAPES, type IndexShape, type IndexSpec } from '@/synth/patch'

const EXAMPLES: { expr: string; what: string }[] = [
  { expr: '6*exp(-10*t) + 1', what: 'a bright pluck that mellows' },
  { expr: 'min(5, 25*t)', what: 'swells brighter, then holds' },
  { expr: '2 + 1.5*sin(2*pi*6*t)', what: 'a 6 Hz shimmer' },
  { expr: '3*abs(sin(2*pi*2*t))', what: 'a pumping wah' },
  { expr: 'f/150*exp(-4*t)', what: 'higher notes get brighter' },
  { expr: '4*exp(-3*t)*(1 + 0.5*sin(2*pi*90*t))', what: 'a decaying growl' },
]

export function IndexEditor({
  spec,
  stash,
  onChange,
}: {
  spec: IndexSpec
  /** The last settings of every shape, so switching back restores them. */
  stash: { [S in IndexShape]: Extract<IndexSpec, { shape: S }> }
  onChange: (spec: IndexSpec) => void
}) {
  const shape = INDEX_SHAPES.find((s) => s.shape === spec.shape)!
  return (
    <div className="flex flex-col gap-4">
      <ToggleGroup
        type="single"
        variant="outline"
        size="sm"
        spacing={0}
        value={spec.shape}
        onValueChange={(v) => v && onChange(stash[v as IndexShape])}
        className="flex w-full flex-wrap"
        aria-label="Shape of I(t)"
      >
        {INDEX_SHAPES.map((s) => (
          <ToggleGroupItem key={s.shape} value={s.shape} className="flex-1 px-2 text-[11px]">
            {s.label}
          </ToggleGroupItem>
        ))}
      </ToggleGroup>
      {spec.shape !== 'formula' && <code className="text-xs text-muted-foreground">{shape.formula}</code>}
      <ShapeParams spec={spec} onChange={onChange} />
    </div>
  )
}

function ShapeParams({ spec, onChange }: { spec: IndexSpec; onChange: (s: IndexSpec) => void }) {
  const I = { min: 0, max: 20, step: 0.01 }
  switch (spec.shape) {
    case 'constant':
      return (
        <ParamSlider symbol="I₀" label="index" {...I} value={spec.value} onChange={(value) => onChange({ ...spec, value })} />
      )
    case 'decay':
      return (
        <>
          <ParamSlider symbol="I₀" label="index at the start" {...I} value={spec.start} onChange={(start) => onChange({ ...spec, start })} />
          <ParamSlider symbol="I₁" label="index it settles to" {...I} value={spec.end} onChange={(end) => onChange({ ...spec, end })} />
          <ParamSlider
            symbol="τ"
            label="time constant (falls 63% per τ)"
            log
            zero
            min={0.002}
            max={5}
            digits={3}
            unit="s"
            value={spec.tau}
            onChange={(tau) => onChange({ ...spec, tau })}
          />
        </>
      )
    case 'envelope':
      return (
        <>
          <ParamSlider symbol="I₀" label="peak index" {...I} value={spec.peak} onChange={(peak) => onChange({ ...spec, peak })} />
          <EnvelopeSliders value={spec} onChange={(e) => onChange({ ...spec, ...e })} />
          <p className="text-[11px] text-muted-foreground">E(t) is an envelope like the volume one, with its own times.</p>
        </>
      )
    case 'wobble':
      return (
        <>
          <ParamSlider symbol="I₀" label="centre index" {...I} value={spec.center} onChange={(center) => onChange({ ...spec, center })} />
          <ParamSlider symbol="a" label="wobble depth" min={0} max={10} value={spec.depth} onChange={(depth) => onChange({ ...spec, depth })} />
          <ParamSlider
            symbol="v"
            label="wobble rate (above ~20 Hz it growls)"
            log
            min={0.1}
            max={200}
            unit="Hz"
            value={spec.rate}
            onChange={(rate) => onChange({ ...spec, rate })}
          />
        </>
      )
    case 'formula':
      return <FormulaField expr={spec.expr} onChange={(expr) => onChange({ shape: 'formula', expr })} />
  }
}

export function EnvelopeSliders({
  value,
  onChange,
}: {
  value: { attack: number; decay: number; sustain: number; release: number }
  onChange: (e: { attack: number; decay: number; sustain: number; release: number }) => void
}) {
  return (
    <>
      <ParamSlider
        symbol="a"
        label="attack: rise time"
        log
        zero
        min={0.001}
        max={2}
        digits={3}
        unit="s"
        value={value.attack}
        onChange={(attack) => onChange({ ...value, attack })}
      />
      <ParamSlider
        symbol="d"
        label="decay: −60 dB toward s"
        log
        zero
        min={0.01}
        max={30}
        digits={2}
        unit="s"
        value={value.decay}
        onChange={(decay) => onChange({ ...value, decay })}
      />
      <ParamSlider
        symbol="s"
        label="sustain level"
        min={0}
        max={1}
        value={value.sustain}
        onChange={(sustain) => onChange({ ...value, sustain })}
      />
      <ParamSlider
        symbol="R"
        label="release: −60 dB after key up"
        log
        zero
        min={0.005}
        max={10}
        digits={3}
        unit="s"
        value={value.release}
        onChange={(release) => onChange({ ...value, release })}
      />
    </>
  )
}

function FormulaField({ expr, onChange }: { expr: string; onChange: (expr: string) => void }) {
  const [text, setText] = useState(expr)
  const result = tryCompile(text)

  const update = (next: string) => {
    setText(next)
    if (tryCompile(next).fn) onChange(next)
  }

  return (
    <div className="flex flex-col gap-2">
      <div className="flex items-center gap-2">
        <span className="shrink-0 text-xs">I(t) =</span>
        <Input
          value={text}
          onChange={(e) => update(e.target.value)}
          spellCheck={false}
          autoComplete="off"
          aria-invalid={result.error ? true : undefined}
          aria-label="Formula for I(t)"
          className="h-8 font-mono text-xs"
        />
      </div>
      {result.error ? (
        <p className="text-[11px] text-destructive" role="alert">
          At character {result.error.pos + 1}: {result.error.message}. Still playing the last formula that worked.
        </p>
      ) : (
        <p className="text-[11px] text-muted-foreground">
          Use t (seconds since key down), f (note Hz), pi, e, + − * / ^ and {FUNCTIONS.join(', ')}.
        </p>
      )}
      <div className="flex flex-wrap gap-1">
        {EXAMPLES.map((ex) => (
          <Button key={ex.expr} variant="outline" size="xs" title={ex.what} onClick={() => update(ex.expr)} className="font-mono text-[10px]">
            {ex.expr}
          </Button>
        ))}
      </div>
    </div>
  )
}
