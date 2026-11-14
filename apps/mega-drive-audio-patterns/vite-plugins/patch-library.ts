// Lets the app read and write the game's patch folder, art/audio/patches/, while it runs
// from `vite` (mise run dev) or `vite preview` (mise run start). A static copy of dist/
// has no server, and the app falls back to downloading the JSON instead.
//
//   GET /api/patches         -> [{ name, patch }]
//   PUT /api/patches/<name>  -> writes art/audio/patches/<name>.json

import { mkdir, readdir, readFile, writeFile } from 'node:fs/promises'
import type { IncomingMessage, ServerResponse } from 'node:http'
import path from 'node:path'
import type { Connect, Plugin } from 'vite'

const FOLDER = path.resolve(import.meta.dirname, '../../../art/audio/patches')
const NAME = /^[a-z0-9_]{1,48}$/
const SHAPES = ['constant', 'decay', 'envelope', 'wobble', 'formula']
const MAX_BYTES = 64 * 1024

function reply(res: ServerResponse, status: number, body: unknown): void {
  res.statusCode = status
  res.setHeader('Content-Type', 'application/json')
  res.end(JSON.stringify(body))
}

function readBody(req: IncomingMessage): Promise<string> {
  return new Promise((resolve, reject) => {
    let size = 0
    const chunks: Buffer[] = []
    req.on('data', (c: Buffer) => {
      size += c.length
      if (size > MAX_BYTES) reject(new Error('patch too large'))
      else chunks.push(c)
    })
    req.on('end', () => resolve(Buffer.concat(chunks).toString('utf8')))
    req.on('error', reject)
  })
}

/** The app checks patches fully; this only keeps junk out of the folder. */
function looksLikePatch(p: unknown): p is Record<string, unknown> {
  if (typeof p !== 'object' || p === null) return false
  const o = p as Record<string, unknown>
  const index = o.index as Record<string, unknown> | undefined
  return (
    o.format === 'fm-patch/1' &&
    typeof o.ratio === 'number' &&
    typeof o.amp === 'object' &&
    typeof index === 'object' &&
    SHAPES.includes(index?.shape as string)
  )
}

async function list(): Promise<{ name: string; patch: unknown }[]> {
  let files: string[] = []
  try {
    files = (await readdir(FOLDER)).filter((f) => f.endsWith('.json')).sort()
  } catch {
    return []
  }
  const out = []
  for (const f of files) {
    try {
      out.push({ name: f.slice(0, -5), patch: JSON.parse(await readFile(path.join(FOLDER, f), 'utf8')) })
    } catch {
      // skip unreadable files; fm.py will complain about them
    }
  }
  return out
}

const handler: Connect.NextHandleFunction = (req, res, next) => {
  const url = new URL(req.url ?? '/', 'http://localhost')
  if (!url.pathname.startsWith('/api/patches')) return next()
  void (async () => {
    try {
      if (req.method === 'GET' && url.pathname === '/api/patches') return reply(res, 200, await list())
      const name = decodeURIComponent(url.pathname.slice('/api/patches/'.length))
      if (req.method === 'PUT' && NAME.test(name)) {
        const patch = JSON.parse(await readBody(req)) as unknown
        if (!looksLikePatch(patch)) return reply(res, 400, { error: 'not an fm-patch/1 patch' })
        await mkdir(FOLDER, { recursive: true })
        const file = path.join(FOLDER, `${name}.json`)
        await writeFile(file, JSON.stringify({ ...patch, name }, null, 2) + '\n')
        return reply(res, 200, { name, file: path.relative(path.resolve(FOLDER, '../../..'), file) })
      }
      reply(res, 404, { error: 'use GET /api/patches or PUT /api/patches/<name>' })
    } catch (e) {
      reply(res, 400, { error: e instanceof Error ? e.message : String(e) })
    }
  })()
}

export function patchLibrary(): Plugin {
  return {
    name: 'patch-library',
    configureServer(server) {
      server.middlewares.use(handler)
    },
    configurePreviewServer(server) {
      server.middlewares.use(handler)
    },
  }
}
