import { useEffect, useMemo, useState } from 'react'
import { api, pageUrl, type Any } from '../api'
import { go } from '../App'
import { I } from '../icons'

function wordDiff(a: string, b: string) {
  const x = a.split(/\s+/), y = b.split(/\s+/)
  const n = x.length, m = y.length
  const dp = Array.from({ length: n + 1 }, () => new Array(m + 1).fill(0))
  for (let i = n - 1; i >= 0; i--) for (let j = m - 1; j >= 0; j--) dp[i][j] = x[i] === y[j] ? dp[i + 1][j + 1] + 1 : Math.max(dp[i + 1][j], dp[i][j + 1])
  const out: { t: 'eq' | 'del' | 'ins'; w: string }[] = []
  let i = 0, j = 0
  while (i < n && j < m) {
    if (x[i] === y[j]) { out.push({ t: 'eq', w: x[i] }); i++; j++ }
    else if (dp[i + 1][j] >= dp[i][j + 1]) out.push({ t: 'del', w: x[i++] })
    else out.push({ t: 'ins', w: y[j++] })
  }
  while (i < n) out.push({ t: 'del', w: x[i++] })
  while (j < m) out.push({ t: 'ins', w: y[j++] })
  return out
}

function Diff({ a, b }: { a: string; b: string }) {
  const d = useMemo(() => wordDiff(a, b), [a, b])
  return (
    <div className="diff small">
      {d.map((p, k) => (p.t === 'eq' ? <span key={k}>{p.w} </span> : p.t === 'del' ? <del key={k}>{p.w} </del> : <ins key={k}>{p.w} </ins>))}
    </div>
  )
}

export default function Changes({ runId, query }: { runId?: string; query: URLSearchParams }) {
  const [cases, setCases] = useState<Any[]>([])
  const [runs, setRuns] = useState<Any[]>([])
  const [data, setData] = useState<Any>(null)
  const [filter, setFilter] = useState<'changes' | 'all'>('changes')
  useEffect(() => {
    api.cases().then(c => setCases(c.subgoal_cases))
    const load = () => api.subgoals().then(setRuns)
    load()
    const t = setInterval(load, 4000)
    return () => clearInterval(t)
  }, [])
  useEffect(() => {
    if (!runId) return setData(null)
    let alive = true
    const load = () => api.subgoal(runId).then(d => alive && setData(d))
    load()
    const t = setInterval(() => (!data || data.status?.stage === 'running') && load(), 3000)
    return () => {
      alive = false
      clearInterval(t)
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [runId, data?.status?.stage])

  const sel = query.get('c')
  if (!runId)
    return (
      <>
        <div className="topbar">
          <h1>Update Impact</h1>
          <span className="muted small">Which requirements must change when a regulation is amended</span>
        </div>
        <div className="content">
          <div className="card">
            <h2>Compare versions</h2>
            {cases.map(c => (
              <div key={c.case_id} className="row" style={{ padding: '10px 0', borderTop: '1px solid var(--border)' }}>
                <div className="stat-icon">{I.changes}</div>
                <div className="grow">
                  <div className="doc-title">{c.case_id}</div>
                  <div className="small muted">old requirements + old / new regulation version</div>
                </div>
                <button className="btn" onClick={async () => go(`changes/${(await api.startSubgoal({ case_id: c.case_id })).run_id}`)}>
                  Analyse changes
                </button>
              </div>
            ))}
          </div>
          <div className="card" style={{ padding: 0, overflow: 'hidden' }}>
            <table className="tbl">
              <thead>
                <tr>
                  <th>Analysis</th>
                  <th>Status</th>
                </tr>
              </thead>
              <tbody>
                {runs.map(r => (
                  <tr key={r.run_id} style={{ cursor: 'pointer' }} onClick={() => go(`changes/${r.run_id}`)}>
                    <td className="doc-title">{r.run_id}</td>
                    <td>
                      <span className={`badge ${r.stage === 'completed' ? 'ok' : r.stage === 'failed' ? 'bad' : 'newver'}`}>{r.stage}</span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      </>
    )

  const al = data?.alignment
  const changes: Any[] = data?.changes?.changes || []
  const byId: Record<string, Any> = Object.fromEntries((al?.rows || []).map((r: Any) => [r.id, r]))
  const items = changes.map((c, k) => ({ ...c, key: `c${k}` }))
  const unchanged = (al?.rows || []).filter((r: Any) => r.status === 'unchanged')
  const cur = items.find(c => c.key === sel) || items[0]
  const counts = { modified: 0, removed: 0, added: 0 } as Record<string, number>
  changes.forEach(c => counts[c.change]++)
  const pick = (k: string) => (window.location.hash = `#/changes/${runId}?c=${k}`)
  return (
    <>
      <div className="topbar">
        <h1>Update Impact · {al?.regulation || ''}</h1>
        {al && (
          <span className="row">
            <span className="chip">
              old <b>{al.old_version}</b>
            </span>
            →
            <span className="chip">
              new <b>{al.new_version}</b>
            </span>
          </span>
        )}
        <div className="spacer" />
        {data?.changes && (
          <a className="btn secondary" href={`/api/subgoal/${runId}/changes.json`}>
            {I.export} Download changes.json
          </a>
        )}
      </div>
      <div className="content">
        <div className="crumbs">
          <a href="#/changes">Update Impact</a> › {runId}
        </div>
        {!al ? (
          <div className="card empty">
            <span className="spinner" /> Aligning old and new versions… {data?.status?.message || ''}
          </div>
        ) : (
          <>
            <div className="stats">
              {[
                ['Old requirements', al.n_old],
                ['Modified', counts.modified],
                ['Removed', counts.removed],
                ['Added', counts.added],
                ['Unchanged', unchanged.length],
              ].map(([l, v]) => (
                <div className="stat" key={l as string}>
                  <div>
                    <div className="stat-label">{l}</div>
                    <div className="stat-value">{v}</div>
                  </div>
                </div>
              ))}
            </div>
            <div className="workspace">
              <div className="pane">
                <div className="pane-head">
                  <div className="pill-toggle">
                    <button className={filter === 'changes' ? 'on' : ''} onClick={() => setFilter('changes')}>
                      Changes
                    </button>
                    <button className={filter === 'all' ? 'on' : ''} onClick={() => setFilter('all')}>
                      + unchanged
                    </button>
                  </div>
                </div>
                <div className="pane-body">
                  {items.map(c => {
                    const row = c.requirement_id ? byId[c.requirement_id] : null
                    return (
                      <div key={c.key} className={`change ${cur?.key === c.key ? 'sel' : ''}`} onClick={() => pick(c.key)} style={{ cursor: 'pointer' }}>
                        <div className="row" style={{ marginBottom: 6 }}>
                          <span className={`badge ${c.change === 'added' ? 'new' : c.change === 'removed' ? 'bad' : 'newver'}`}>{c.change}</span>
                          {c.requirement_id && <span className="chip">{c.requirement_id}</span>}
                          {c.source?.paragraph && (
                            <span className="chip">
                              § <b>{c.source.paragraph}</b>
                            </span>
                          )}
                          {row && row.old?.label !== row.new?.label && row.new && <span className="small muted">formerly § {row.old?.label}</span>}
                        </div>
                        {c.change === 'modified' && row ? (
                          <Diff a={row.text} b={c.new_text} />
                        ) : (
                          <div className="small">{c.new_text || row?.text}</div>
                        )}
                      </div>
                    )
                  })}
                  {filter === 'all' &&
                    unchanged.map((r: Any) => (
                      <div key={r.id} className="change" style={{ opacity: 0.6 }}>
                        <div className="row" style={{ marginBottom: 6 }}>
                          <span className="badge grey">unchanged</span>
                          <span className="chip">{r.id}</span>
                          {r.old?.label !== r.new?.label && (
                            <span className="small muted">
                              moved § {r.old?.label} → § {r.new?.label}
                            </span>
                          )}
                        </div>
                        <div className="small">{r.text}</div>
                      </div>
                    ))}
                </div>
              </div>
              <div className="pane">
                {cur && (
                  <>
                    <div className="pane-head">
                      <b>Reason</b>
                    </div>
                    <div className="pane-body" style={{ padding: 14 }}>
                      <div className="evidence" style={{ marginBottom: 12 }}>
                        {cur.reason}
                      </div>
                      {cur.requirement_id && byId[cur.requirement_id] && (
                        <div style={{ marginBottom: 12 }}>
                          <div className="small muted">Old source § {byId[cur.requirement_id].old?.label} → new § {byId[cur.requirement_id].new?.label}</div>
                          {byId[cur.requirement_id].new && <Diff a={byId[cur.requirement_id].old?.text || ''} b={byId[cur.requirement_id].new?.text || ''} />}
                        </div>
                      )}
                      {cur.source?.page ? (
                        <img className="viewer-img" src={pageUrl(data.case_id, 'new', cur.source.page, cur.source.paragraph, (cur.new_text || '').slice(0, 0))} />
                      ) : (
                        byId[cur.requirement_id]?.old && (
                          <img className="viewer-img" src={pageUrl(data.case_id, 'old', byId[cur.requirement_id].old.pages[0], byId[cur.requirement_id].old.label)} />
                        )
                      )}
                    </div>
                  </>
                )}
              </div>
            </div>
          </>
        )}
      </div>
    </>
  )
}
