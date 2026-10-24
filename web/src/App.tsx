import { useEffect, useState } from 'react'
import { I } from './icons'
import { api } from './api'
import Projects from './pages/Projects'
import RunView from './pages/RunView'
import Library from './pages/Library'
import Changes from './pages/Changes'

export type Route = { path: string[]; query: URLSearchParams }

function parse(): Route {
  const h = window.location.hash.replace(/^#\/?/, '')
  const [p, q] = h.split('?')
  return { path: p ? p.split('/').map(decodeURIComponent) : [], query: new URLSearchParams(q || '') }
}

export function go(path: string) {
  window.location.hash = path.startsWith('#') ? path : `#/${path}`
}

export default function App() {
  const [route, setRoute] = useState<Route>(parse())
  const [usage, setUsage] = useState<{ total_usd: number; model: string } | null>(null)
  useEffect(() => {
    const on = () => setRoute(parse())
    window.addEventListener('hashchange', on)
    return () => window.removeEventListener('hashchange', on)
  }, [])
  useEffect(() => {
    api.usage().then(setUsage).catch(() => {})
    const t = setInterval(() => api.usage().then(setUsage).catch(() => {}), 15000)
    return () => clearInterval(t)
  }, [])

  const top = route.path[0] || 'projects'
  let page
  if (top === 'runs' && route.path[1]) page = <RunView runId={route.path[1]} tab={route.path[2] || 'dashboard'} query={route.query} />
  else if (top === 'library') page = <Library />
  else if (top === 'changes') page = <Changes runId={route.path[1]} query={route.query} />
  else page = <Projects />

  const nav = [
    { key: 'projects', label: 'Projects', icon: I.projects, beta: true },
    { key: 'library', label: 'Regulations', icon: I.browse },
    { key: 'changes', label: 'Update Impact', icon: I.changes },
  ]
  return (
    <div className="shell">
      <aside className="sidebar">
        <div className="brand">
          <div className="brand-mark">✱</div>
          <div>
            <div className="brand-name">certivity</div>
            <div className="brand-sub">Requirements Agent</div>
          </div>
        </div>
        <nav className="nav">
          {nav.map(n => (
            <a key={n.key} href={`#/${n.key}`} className={top === n.key || (n.key === 'projects' && top === 'runs') ? 'active' : ''}>
              {n.icon}
              <span>{n.label}</span>
              {n.beta && <span className="beta">AGENT</span>}
            </a>
          ))}
        </nav>
        <div className="sidebar-foot">
          {usage && (
            <div style={{ marginBottom: 6 }}>
              {usage.model}
              <br />
              Claude spend: ${usage.total_usd.toFixed(2)}
            </div>
          )}
          Industrial Agents Hackathon · Munich 2026
        </div>
      </aside>
      <main className="main">{page}</main>
    </div>
  )
}
