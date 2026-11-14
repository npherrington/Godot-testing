// The built-in patches. Each is a JSON file in ./presets/, which art/audio/fm.py also
// reads, so a preset can be used in the game by name without saving it first.

import { readPatch, type Patch } from './patch'

const files = import.meta.glob<{ default: unknown }>('./presets/*.json', { eager: true })

const ORDER = [
  'electric_piano',
  'slap_bass',
  'brass',
  'saw_lead',
  'reed',
  'organ',
  'bell',
  'metal_hit',
  'monster_growl',
]

export const PRESETS: Patch[] = Object.values(files)
  .map((m) => readPatch(m.default))
  .sort((a, b) => {
    const ia = ORDER.indexOf(a.name)
    const ib = ORDER.indexOf(b.name)
    return (ia < 0 ? 99 : ia) - (ib < 0 ? 99 : ib) || a.name.localeCompare(b.name)
  })

export function titleOf(name: string): string {
  return name.replace(/_/g, ' ').replace(/^\w/, (c) => c.toUpperCase())
}
