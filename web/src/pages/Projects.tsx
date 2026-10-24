import { useEffect, useState } from 'react'
import { api, type Any } from '../api'
import { go } from '../App'
import { I } from '../icons'

export function StageBadge({ stage }: { stage?: string }) {
  if (!stage) return null
  const cls = stage === 'completed' ? 'ok' : stage === 'failed' ? 'bad' : stage === 'partial' ? 'warn' : 'newver'
  const running = !['completed', 'failed', 'partial'].includes(stage)
  return (
    <span className={`badge ${cls}`}>
      {running && <span className="spinner" style={{ width: 10, height: 10 }} />}
      {stage}
    </span>
  )
}

export default function Projects() {
  const [cases, setCases] = useState<Any>(null)
  const [runs, setRuns] = useState<Any[]>([])
  const [deep, setDeep] = useState(false)
  const [audit, setAudit] = useState(false)
  const [specText, setSpecText] = useState('')
  const [files, setFiles] = useState<File[]>([])
  const [name, setName] = useState('custom-product')
  const [busy, setBusy] = useState(false)

  useEffect(() => {
    api.cases().then(setCases)
    const load = () => api.runs().then(setRuns).catch(() => {})
    load()
    const t = setInterval(load, 4000)
    return () => clearInterval(t)
  }, [])

  async function start(case_id: string) {
    setBusy(true)
    try {
      const r = await api.startRun({ case_id, deep_image: deep, audit })
      go(`runs/${r.run_id}`)
    } finally {
      setBusy(false)
    }
  }

  async function startUpload() {
    const fd = new FormData()
    fd.append('case_id', name || 'custom-product')
    fd.append('spec_text', specText)
    fd.append('deep_image', String(deep || (!specText.trim() && !files.some(f => /\.(md|txt)$/i.test(f.name)))))
    fd.append('audit', String(audit))
    files.forEach(f => fd.append('files', f))
    setBusy(true)
    try {
      const r = await api.startUpload(fd)
      go(`runs/${r.run_id}`)
    } finally {
      setBusy(false)
    }
  }

  return (
    <>
      <div className="topbar">
        <h1>Projects</h1>
        <div className="spacer" />
        <span className="muted small">From a product specification to the requirements it must fulfil</span>
      </div>
      <div className="content">
        <div className="grid2">
          <div className="card">
            <h2>Start from a case</h2>
            <div className="row wrap" style={{ marginBottom: 12 }}>
              <label className="row small">
                <input type="checkbox" checked={audit} onChange={e => setAudit(e.target.checked)} /> Independent omission audit (second
                model pass; measured +3 correct / 63 added on dev)
              </label>
              <label className="row small">
                <input type="checkbox" checked={deep} onChange={e => setDeep(e.target.checked)} /> Deep image analysis
              </label>
            </div>
            {cases?.cases.map((c: Any) => (
              <div key={c.case_id} className="row" style={{ padding: '10px 0', borderTop: '1px solid var(--border)' }}>
                <div className="stat-icon">{I.projects}</div>
                <div className="grow">
                  <div className="doc-title">{c.case_id}</div>
                  <div className="doc-meta">
                    {c.files.map((f: string) => (
                      <span key={f} className="chip">
                        {f}
                      </span>
                    ))}
                  </div>
                </div>
                <button className="btn" disabled={busy} onClick={() => start(c.case_id)}>
                  Analyse
                </button>
              </div>
            ))}
          </div>
          <div className="card">
            <h2>New product</h2>
            <div className="row" style={{ marginBottom: 8 }}>
              <span className="small muted" style={{ width: 90 }}>
                Project id
              </span>
              <input type="text" value={name} onChange={e => setName(e.target.value)} style={{ flex: 1 }} />
            </div>
            <textarea rows={6} placeholder="Paste the technical specification (optional if you upload a drawing)…" value={specText}
              onChange={e => setSpecText(e.target.value)} />
            <label className="drop" style={{ display: 'block', marginTop: 8, cursor: 'pointer' }}>
              <input type="file" multiple style={{ display: 'none' }} accept=".png,.jpg,.jpeg,.webp,.md,.txt"
                onChange={e => setFiles(Array.from(e.target.files || []))} />
              {files.length ? files.map(f => f.name).join(', ') : 'Drop or choose an exploded view (PNG/JPG) and/or a spec file (MD/TXT)'}
            </label>
            <div className="row" style={{ marginTop: 10 }}>
              <span className="small muted grow">Drawing only? Deep image analysis switches on automatically.</span>
              <button className="btn" disabled={busy || (!specText.trim() && !files.length)} onClick={startUpload}>
                Analyse product
              </button>
            </div>
          </div>
        </div>

        <div className="card" style={{ marginTop: 14, padding: 0, overflow: 'hidden' }}>
          <div style={{ padding: '14px 18px' }}>
            <h2 style={{ margin: 0 }}>Analyses</h2>
          </div>
          <table className="tbl">
            <thead>
              <tr>
                <th>Run</th>
                <th>Status</th>
                <th>Progress</th>
                <th>Requirements</th>
                <th>Updated</th>
              </tr>
            </thead>
            <tbody>
              {runs.map(r => (
                <tr key={r.run_id} style={{ cursor: 'pointer' }} onClick={() => go(`runs/${r.run_id}`)}>
                  <td>
                    <div className="doc-title">{r.run_id}</div>
                    <div className="small muted">{r.message}</div>
                  </td>
                  <td>
                    <StageBadge stage={r.stage} />
                  </td>
                  <td style={{ width: 160 }}>
                    <div className="progress">
                      <div style={{ width: `${Math.round((r.progress ?? (r.stage === 'completed' ? 1 : 0)) * 100)}%` }} />
                    </div>
                  </td>
                  <td>{r.n_requirements ?? '–'}</td>
                  <td className="small muted">{r.updated ? new Date(r.updated).toLocaleString() : ''}</td>
                </tr>
              ))}
              {!runs.length && (
                <tr>
                  <td colSpan={5} className="empty">
                    No analyses yet
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </div>
    </>
  )
}
