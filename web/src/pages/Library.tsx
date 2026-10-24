import { useEffect, useState } from 'react'
import { api, pageUrl, pdfUrl, type Any } from '../api'
import { I } from '../icons'

export default function Library() {
  const [regs, setRegs] = useState<Any[]>([])
  const [q, setQ] = useState('')
  const [open, setOpen] = useState<Any>(null)
  useEffect(() => {
    api.regulations().then(setRegs)
  }, [])
  const list = regs.filter(r => !q || `${r.regulation} ${r.title}`.toLowerCase().includes(q.toLowerCase()))
  const newer = regs.filter(r => r.latest).length
  return (
    <>
      <div className="topbar">
        <h1>Regulatory Library</h1>
        <span className="muted small">{regs.length} regulations · base versions are the analysis baseline</span>
        <div className="spacer" />
        <span className="badge newver">{newer} with a newer version in the package</span>
      </div>
      <div className="content">
        {open ? (
          <Browse reg={open} onClose={() => setOpen(null)} />
        ) : (
          <>
            <div className="row" style={{ marginBottom: 12 }}>
              <div className="search grow">
                {I.search}
                <input type="text" placeholder="Filter by document identifier or title" value={q} onChange={e => setQ(e.target.value)} />
              </div>
            </div>
            <div className="card" style={{ padding: 0, overflow: 'hidden' }}>
              <table className="tbl">
                <thead>
                  <tr>
                    <th>Document</th>
                    <th>Update type</th>
                    <th>Freshness</th>
                    <th />
                  </tr>
                </thead>
                <tbody>
                  {list.map(r => (
                    <tr key={r.regulation}>
                      <td>
                        <div className="doc-title" style={{ cursor: 'pointer' }} onClick={() => setOpen(r)}>
                          {r.regulation} - {r.title}
                        </div>
                        <div className="doc-meta">
                          <span className="chip">
                            Version: <b>{r.base.version_label}</b>
                          </span>
                          <span className="chip">
                            Status: <b>{r.base.status}</b>
                          </span>
                        </div>
                        <div className="small muted" style={{ marginTop: 6 }}>
                          UNECE › UN-R
                        </div>
                      </td>
                      <td>{r.latest ? <span className="badge newver">New Version {r.latest.version_label}</span> : <span className="muted">–</span>}</td>
                      <td>
                        {r.latest ? (
                          <span className="row small">
                            <span className="dot red" /> newer version known ({r.latest.status})
                          </span>
                        ) : (
                          <span className="row small">
                            <span className="dot grey" /> no newer version in package (not checked online)
                          </span>
                        )}
                      </td>
                      <td style={{ whiteSpace: 'nowrap' }}>
                        <button className="btn ghost small" onClick={() => setOpen(r)}>
                          Browse
                        </button>{' '}
                        <a className="btn ghost small" href={pdfUrl(r.regulation, 'base')} target="_blank">
                          PDF
                        </a>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </>
        )}
      </div>
    </>
  )
}

function Browse({ reg, onClose }: { reg: Any; onClose: () => void }) {
  const [role, setRole] = useState('base')
  const [outline, setOutline] = useState<Any[]>([])
  const [page, setPage] = useState(1)
  const [label, setLabel] = useState('')
  const [meta, setMeta] = useState<Any>(null)
  useEffect(() => {
    api.outline(reg.regulation, role).then(setOutline)
    api.docMeta(reg.regulation, role).then(setMeta)
    setPage(1)
  }, [reg.regulation, role])
  return (
    <>
      <div className="crumbs">
        <a onClick={onClose} style={{ cursor: 'pointer' }}>
          Browse
        </a>{' '}
        › UNECE › UN-R › {reg.regulation} › {role === 'base' ? reg.base.version_label : reg.latest?.version_label}
      </div>
      <div className="row" style={{ marginBottom: 12 }}>
        <h2 className="grow">
          {reg.regulation} • {reg.title}
        </h2>
        <div className="pill-toggle">
          <button className={role === 'base' ? 'on' : ''} onClick={() => setRole('base')}>
            base {reg.base.version_label}
          </button>
          {reg.latest && (
            <button className={role === 'latest' ? 'on' : ''} onClick={() => setRole('latest')}>
              latest {reg.latest.version_label}
            </button>
          )}
        </div>
        <button className="btn ghost" onClick={onClose}>
          Close
        </button>
      </div>
      <div className="workspace" style={{ gridTemplateColumns: '340px 1fr' }}>
        <div className="pane">
          <div className="pane-body">
            {outline.map((o, i) => (
              <div
                key={i}
                className={`req ${label === o.label ? 'sel' : ''}`}
                style={{ marginLeft: o.kind === 'para' ? 18 : 0, padding: '5px 8px' }}
                onClick={() => {
                  setPage(o.page)
                  setLabel(o.label)
                }}
              >
                <span className="small">
                  <b>{o.label}</b> {o.title}
                </span>
              </div>
            ))}
          </div>
        </div>
        <div className="pane">
          <div className="pane-head">
            <button className="btn ghost small" onClick={() => setPage(Math.max(1, page - 1))}>
              ‹
            </button>
            <span className="small">
              page {page} / {meta?.page_count}
            </span>
            <button className="btn ghost small" onClick={() => setPage(page + 1)}>
              ›
            </button>
            <span className="grow" />
            <span className="mono muted">sha256 {meta?.sha256?.slice(0, 12)}…</span>
          </div>
          <div className="pane-body">
            <img className="viewer-img" src={pageUrl(reg.regulation, role, page, label)} />
          </div>
        </div>
      </div>
    </>
  )
}
