import path from 'node:path'
import tailwindcss from '@tailwindcss/vite'
import react from '@vitejs/plugin-react'
import { defineConfig } from 'vite'
import { patchLibrary } from './vite-plugins/patch-library.ts'

export default defineConfig({
  plugins: [react(), tailwindcss(), patchLibrary()],
  resolve: {
    alias: { '@': path.resolve(import.meta.dirname, './src') },
  },
  // Dev and preview listen on localhost only: the patch API writes into the repo.
  server: { host: 'localhost', port: 5173 },
  preview: { host: 'localhost', port: 4173 },
})
