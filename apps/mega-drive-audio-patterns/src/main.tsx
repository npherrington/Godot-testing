import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import './index.css'
import App from './App.tsx'

// Dark unless the viewer picked light (the theme button remembers it) or the OS is light.
let theme: string | null = null
try {
  theme = localStorage.getItem('theme')
} catch {
  // storage blocked: follow the OS
}
const dark = theme ? theme === 'dark' : !window.matchMedia('(prefers-color-scheme: light)').matches
document.documentElement.classList.toggle('dark', dark)

createRoot(document.getElementById('root')!).render(
  <StrictMode>
    <App />
  </StrictMode>,
)
