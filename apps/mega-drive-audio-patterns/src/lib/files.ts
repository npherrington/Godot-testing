// Saving and opening files in the browser, and the dev server's patch API.

import { readPatch, slug, type Patch } from '@/synth/patch'

export function download(name: string, data: BlobPart, type: string): void {
  const url = URL.createObjectURL(new Blob([data], { type }))
  const a = document.createElement('a')
  a.href = url
  a.download = name
  a.click()
  setTimeout(() => URL.revokeObjectURL(url), 1000)
}

export function openJson(): Promise<unknown> {
  return new Promise((resolve, reject) => {
    const input = document.createElement('input')
    input.type = 'file'
    input.accept = '.json,application/json'
    input.onchange = async () => {
      const file = input.files?.[0]
      if (!file) return
      try {
        resolve(JSON.parse(await file.text()))
      } catch (e) {
        reject(e)
      }
    }
    input.click()
  })
}

/** Patches saved in art/audio/patches/, or null when there's no dev server to ask. */
export async function listSaved(): Promise<Patch[] | null> {
  try {
    const res = await fetch('/api/patches')
    if (!res.ok || !res.headers.get('content-type')?.includes('json')) return null
    const items = (await res.json()) as { name: string; patch: unknown }[]
    const out: Patch[] = []
    for (const it of items) {
      try {
        out.push({ ...readPatch(it.patch), name: it.name })
      } catch {
        // not a valid patch; skip it
      }
    }
    return out
  } catch {
    return null
  }
}

/** Write a patch to art/audio/patches/<name>.json. Returns the repo path, or null without a server. */
export async function saveToRepo(patch: Patch): Promise<string | null> {
  const name = slug(patch.name)
  try {
    const res = await fetch(`/api/patches/${name}`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ ...patch, name }),
    })
    if (!res.ok) return null
    return ((await res.json()) as { file: string }).file
  } catch {
    return null
  }
}

const KEY = 'mega-drive-audio-patterns.patch'

export function loadDraft(): Patch | null {
  try {
    const raw = localStorage.getItem(KEY)
    return raw ? readPatch(JSON.parse(raw)) : null
  } catch {
    return null
  }
}

export function saveDraft(p: Patch): void {
  try {
    localStorage.setItem(KEY, JSON.stringify(p))
  } catch {
    // private mode or storage full: the draft just isn't remembered
  }
}
