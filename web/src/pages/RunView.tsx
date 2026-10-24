import { useEffect, useMemo, useState } from 'react'
import { api, pageUrl, pdfUrl, type Any } from '../api'
import { go } from '../App'
import { I } from '../icons'
import { StageBadge } from './Projects'

const TABS = [
  ['dashboard', 'Dashboard'],
  ['product', 'Product'],
  ['requirements', 'Requirements'],
  ['regulations', 'Regulations'],
  ['coverage', 'Coverage'],
  ['export', 'Export'],
]

export default function RunView({ runId, tab, query }: { runId: string; tab: string; query: URLSearchParams }) {
  const [run, setRun] = useState<Any>(null)
  const [reqs, setReqs] = useState<Any[]>([])
  useEffect(() => {
    let alive = true
    const load = async () => {
      const r = await api.run(runId).catch(() => null)
      if (!alive || !r) return
      setRun(r)
      if (['completed', 'partial', 'finalizing'].includes(r.status?.stage)) setReqs(await api.requirements(runId))
    }
    load()
    const t = setInterval(() => {
      if (!run || !['completed', 'partial', 'failed'].includes(run?.status?.stage)) load()
    }, 3000)
    return () => {
      alive = false
      clearInterval(t)
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [runId, run?.status?.stage])

  const st = run?.status
  const title = run?.profile?.product_name || run?.inputs?.case_id || runId
  return (
    <>
      <div className="topbar">
        <h1>{title}</h1>
        <StageBadge stage={st?.stage} />
        <div className="spacer" />
        {st && !['completed', 'partial', 'failed'].includes(st.stage) && (
          <div className="row" style={{ width: 320 }}>
            <span className="small muted grow" style={{ whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>
              {st.message}
            </span>
            <div className="progress" style={{ width: 120 }}>
              <div style={{ width: `${Math.round((st.progress || 0) * 100)}%` }} />
            </div>
          </div>
        )}
        {st && <span className="chip">${(st.spent_usd || 0).toFixed(2)}</span>}
      </div>
      <div className="content">
        <div className="crumbs">
          <a href="#/projects">⌂</a> › <a href="#/projects">Projects</a> › <span>{run?.inputs?.case_id || runId}</span>
        </div>
        <div className="tabs">
          {TABS.map(([k, label]) => (
            <a key={k} href={`#/runs/${runId}/${k}`} className={tab === k ? 'active' : ''}>
              {label}
              {k === 'product' && run?.profile?.questions?.length ? <span className="tab-badge">{run.profile.questions.length}</span> : null}
            </a>
          ))}
        </div>
        {!run ? (
          <div className="empty">
            <span className="spinner" />
          </div>
        ) : tab === 'product' ? (
          <Product run={run} />
        ) : tab === 'requirements' ? (
          <Requirements run={run} reqs={reqs} query={query} />
        ) : tab === 'regulations' ? (
          <Screening run={run} reqs={reqs} />
        ) : tab === 'coverage' ? (
          <Coverage run={run} />
        ) : tab === 'export' ? (
          <Export run={run} reqs={reqs} />
        ) : (
          <Dashboard run={run} reqs={reqs} />
        )}
      </div>
    </>
  )
}

/* ------------------------------------------------------------------ dashboard */
function Stats({ run, reqs }: { run: Any; reqs: Any[] }) {
  const exported = reqs.filter(r => r.exported)
  const applicable = (run.screening || []).filter((d: Any) => d.decision === 'applicable').length
  const pages = new Set(exported.map(r => `${r.regulation}|${r.page}`)).size
  const items = [
    [I.doc, 'Regulations screened', run.screening?.length ?? '–'],
    [I.check, 'Applicable regulations', run.screening ? applicable : '–'],
    [I.list, 'Requirements', reqs.length ? exported.length : '–'],
    [I.page, 'Pages cited', reqs.length ? pages : '–'],
    [I.coin, 'Claude cost', `$${(run.status?.spent_usd || 0).toFixed(2)}`],
  ]
  return (
    <div className="stats">
      {items.map(([icon, label, value], i) => (
        <div className="stat" key={i}>
          <div className="stat-icon">{icon}</div>
          <div>
            <div className="stat-label">{label as string}</div>
            <div className="stat-value">{value as string}</div>
          </div>
        </div>
      ))}
    </div>
  )
}

function Dashboard({ run, reqs }: { run: Any; reqs: Any[] }) {
  const byReg = useMemo(() => {
    const m: Record<string, number> = {}
    reqs.filter(r => r.exported).forEach(r => (m[r.regulation] = (m[r.regulation] || 0) + 1))
    return m
  }, [reqs])
  const sel = (run.screening || []).filter((d: Any) => d.decision !== 'not_applicable')
  return (
    <>
      <Stats run={run} reqs={reqs} />
      <div className="grid2">
        <div className="card">
          <h2>Applicable regulations</h2>
          {sel.map((d: Any, i: number) => (
            <div className="group" key={d.regulation}>
              <div className={`group-bar g${i % 8}`} onClick={() => go(`runs/${run.run_id}/requirements?reg=${encodeURIComponent(d.regulation)}`)}>
                <span>
                  {d.regulation} · {d.title}
                </span>
                {d.decision === 'potentially_applicable' && <span className="badge warn">conditional</span>}
                <span className="count">{byReg[d.regulation] ?? 0}</span>
              </div>
            </div>
          ))}
          {!sel.length && <div className="muted">Screening not finished yet.</div>}
        </div>
        <div className="card">
          <h2>Activity</h2>
          <div style={{ maxHeight: 380, overflow: 'auto' }}>
            {[...(run.status?.events || [])].reverse().map((e: Any, i: number) => (
              <div key={i} className="row small" style={{ padding: '5px 0', borderBottom: '1px solid var(--border)' }}>
                <span className="muted mono" style={{ width: 70 }}>
                  {new Date(e.t).toLocaleTimeString()}
                </span>
                <span className="badge grey">{e.stage}</span>
                <span className="grow">{e.message}</span>
              </div>
            ))}
          </div>
        </div>
      </div>
    </>
  )
}

/* ------------------------------------------------------------------ product */
function Product({ run }: { run: Any }) {
  const p = run.profile
  return (
    <div className="grid2" style={{ alignItems: 'start' }}>
      <div>
        <div className="card">
          <h2>Inputs</h2>
          {run.inputs?.image_urls?.map((u: string) => (
            <img key={u} src={u} className="viewer-img" style={{ marginBottom: 10 }} />
          ))}
          {run.inputs?.spec ? (
            <pre style={{ whiteSpace: 'pre-wrap', fontFamily: 'var(--font)', fontSize: 13, margin: 0 }}>{run.inputs.spec}</pre>
          ) : (
            <div className="muted">No written specification: profile built from the drawing only.</div>
          )}
        </div>
      </div>
      <div>
        {!p ? (
          <div className="card empty">
            <span className="spinner" /> Building product profile…
          </div>
        ) : (
          <>
            <div className="card">
              <h2>{p.product_name}</h2>
              <div className="muted" style={{ marginBottom: 10 }}>
                {p.product_type} · {p.vehicle_categories.join(', ') || 'vehicle category unknown'}
              </div>
              <div>{p.summary}</div>
              <div className="row wrap" style={{ marginTop: 10, gap: 6 }}>
                {p.functions.map((f: string) => (
                  <span className="chip" key={f}>
                    {f}
                  </span>
                ))}
              </div>
            </div>
            <div className="card">
              <h2>Components</h2>
              {p.components.map((c: Any, i: number) => (
                <div key={i} className="row" style={{ padding: '6px 0', borderBottom: '1px solid var(--border)' }}>
                  <div className="grow">
                    <b>{c.name}</b> <span className="muted">— {c.function}</span>
                  </div>
                  <span className={`ep ${c.status}`}>{c.status.replace('_', ' ')}</span>
                </div>
              ))}
            </div>
            <div className="card">
              <h2>Facts</h2>
              <div className="row small" style={{ gap: 8, marginBottom: 8 }}>
                {['spec_stated', 'observed', 'inferred', 'unknown'].map(s => (
                  <span key={s} className={`ep ${s}`}>
                    {s.replace('_', ' ')}
                  </span>
                ))}
              </div>
              {p.facts.map((f: Any, i: number) => (
                <div key={i} style={{ padding: '6px 0', borderBottom: '1px solid var(--border)' }}>
                  <div className="row">
                    <span className="grow">
                      <span className="muted">{f.attribute}:</span> <b>{f.value || '—'}</b>
                    </span>
                    <span className={`ep ${f.status}`}>{f.status.replace('_', ' ')}</span>
                  </div>
                  {f.note && <div className="small muted">{f.note}</div>}
                </div>
              ))}
            </div>
            {(p.unknowns.length > 0 || p.questions.length > 0) && (
              <div className="card">
                <h2>Open questions</h2>
                {p.questions.map((q: Any, i: number) => (
                  <div key={i} style={{ marginBottom: 8 }}>
                    <b>{q.question}</b>
                    <div className="small muted">{q.why_it_matters}</div>
                  </div>
                ))}
                {p.unknowns.map((u: string, i: number) => (
                  <div key={i} className="small">
                    <span className="ep unknown">unknown</span> {u}
                  </div>
                ))}
              </div>
            )}
          </>
        )}
      </div>
    </div>
  )
}

/* ------------------------------------------------------------------ requirements workspace */
function Requirements({ run, reqs, query }: { run: Any; reqs: Any[]; query: URLSearchParams }) {
  const [q, setQ] = useState('')
  const [mode, setMode] = useState<'exported' | 'all'>('exported')
  const [collapsed, setCollapsed] = useState<Record<string, boolean>>({})
  const selId = query.get('r')
  const regFilter = query.get('reg')
  const list = reqs.filter(
    r =>
      (mode === 'all' || r.exported) &&
      (!regFilter || r.regulation === regFilter) &&
      (!q || `${r.text} ${r.paragraph} ${r.regulation}`.toLowerCase().includes(q.toLowerCase())),
  )
  const groups = useMemo(() => {
    const m = new Map<string, Any[]>()
    list.forEach(r => m.set(r.regulation, [...(m.get(r.regulation) || []), r]))
    return [...m.entries()]
  }, [list])
  const sel = reqs.find(r => r.id === selId) || list[0]
  const titles: Record<string, string> = Object.fromEntries((run.screening || []).map((d: Any) => [d.regulation, d.title]))
  const select = (id: string) => {
    const qs = new URLSearchParams(query)
    qs.set('r', id)
    window.location.hash = `#/runs/${run.run_id}/requirements?${qs}`
  }

  if (!reqs.length)
    return (
      <div className="card empty">
        <span className="spinner" /> Requirements appear here when the analysis finishes ({run.status?.message})
      </div>
    )
  return (
    <>
      <Stats run={run} reqs={reqs} />
      <div className="workspace">
        <div className="pane">
          <div className="pane-head">
            <div className="search grow">
              {I.search}
              <input type="text" placeholder="Search requirements…" value={q} onChange={e => setQ(e.target.value)} />
            </div>
            <div className="pill-toggle">
              <button className={mode === 'exported' ? 'on' : ''} onClick={() => setMode('exported')}>
                Exported
              </button>
              <button className={mode === 'all' ? 'on' : ''} onClick={() => setMode('all')}>
                All candidates
              </button>
            </div>
            {regFilter && (
              <a className="chip" href={`#/runs/${run.run_id}/requirements`}>
                {regFilter} ✕
              </a>
            )}
          </div>
          <div className="pane-body">
            {groups.map(([reg, rs], gi) => (
              <div className="group" key={reg}>
                <div className={`group-bar g${gi % 8}`} onClick={() => setCollapsed({ ...collapsed, [reg]: !collapsed[reg] })}>
                  <span className="caret">{collapsed[reg] ? '›' : '⌄'}</span>
                  <span>
                    {reg} · {titles[reg] || ''}
                  </span>
                  <span className="count">{rs.length}</span>
                </div>
                {!collapsed[reg] &&
                  rs.map(r => (
                    <div key={r.id} className={`req ${sel?.id === r.id ? 'sel' : ''} ${r.exported ? '' : 'dim'}`} onClick={() => select(r.id)}>
                      <div className="req-text">{r.text}</div>
                      <div className="req-meta">
                        <span className="chip">
                          § <b>{r.paragraph}</b>
                        </span>
                        <span className="chip">
                          p. <b>{r.page}</b>
                        </span>
                        <span className="chip">
                          v <b>{r.version}</b>
                        </span>
                        {r.applicability === 'conditional' && <span className="badge warn">conditional</span>}
                        {r.pass === 'audit' && <span className="badge newver">found by audit</span>}
                        {!r.exported && <span className="badge grey">below threshold</span>}
                        <span className="small muted" style={{ marginLeft: 'auto' }}>
                          {r.id}
                        </span>
                      </div>
                    </div>
                  ))}
              </div>
            ))}
          </div>
        </div>
        <div className="pane">{sel ? <Evidence run={run} r={sel} /> : <div className="empty">Select a requirement</div>}</div>
      </div>
    </>
  )
}

function Evidence({ run, r }: { run: Any; r: Any }) {
  const [page, setPage] = useState<number>(r.page)
  const [para, setPara] = useState<Any>(null)
  const [reviews, setReviews] = useState<Any[]>([])
  const decision = (run.screening || []).find((d: Any) => d.regulation === r.regulation)
  useEffect(() => {
    setPage(r.page)
    setPara(null)
    api.paragraph(r.regulation, 'base', r.paragraph).then(setPara).catch(() => {})
    api.reviews(run.run_id).then(setReviews).catch(() => {})
  }, [r.id, r.regulation, r.paragraph, r.page, run.run_id])
  const mine = reviews.filter(x => x.requirement_id === r.id)
  const last = mine[mine.length - 1]
  const act = async (action: string) => {
    await api.review(run.run_id, { requirement_id: r.id, action })
    setReviews(await api.reviews(run.run_id))
  }
  return (
    <>
      <div className="pane-head">
        <span className="doc-title">{r.regulation}</span>
        <span className="chip">
          Version: <b>{r.version}</b>
        </span>
        <span className="chip">
          §<b>{r.paragraph}</b>
        </span>
        <span className="badge newver">base</span>
        <div className="grow" />
        <button className="btn ghost small" onClick={() => setPage(Math.max(1, page - 1))}>
          ‹
        </button>
        <span className="small">p. {page}</span>
        <button className="btn ghost small" onClick={() => setPage(page + 1)}>
          ›
        </button>
        <a className="btn ghost small" href={pdfUrl(r.regulation, 'base', page)} target="_blank">
          PDF {I.ext}
        </a>
      </div>
      <div className="pane-body" style={{ padding: 14 }}>
        <div style={{ fontSize: 15, fontWeight: 500, marginBottom: 10 }}>{r.text}</div>
        <div className="kv" style={{ marginBottom: 10 }}>
          <span className="k">Source quote</span>
          <span className="evidence">“{r.quote}”</span>
          {decision && (
            <>
              <span className="k">Why applicable</span>
              <span>{decision.reason}</span>
            </>
          )}
          {r.applicability === 'conditional' && (
            <>
              <span className="k">Condition</span>
              <span>
                <span className="badge warn">open fact</span> {r.condition}
              </span>
            </>
          )}
          {r.test_case && (
            <>
              <span className="k">Proposed test</span>
              <span>{r.test_case}</span>
            </>
          )}
          <span className="k">Confidence</span>
          <span>
            {Math.round(r.probability * 100)}% {r.pass === 'audit' ? '· added by independent audit' : ''}
          </span>
        </div>
        <div className="row" style={{ marginBottom: 12 }}>
          <button className="btn small" onClick={() => act('accept')}>
            Accept
          </button>
          <button className="btn ghost small" onClick={() => act('reject')}>
            Reject
          </button>
          {last && (
            <span className={`badge ${last.action === 'accept' ? 'ok' : 'bad'}`}>
              {last.action}ed {new Date(last.t).toLocaleTimeString()}
            </span>
          )}
          <span className="grow" />
          <button
            className="btn ghost small"
            onClick={() => navigator.clipboard.writeText(window.location.href)}
            title="Copy link to this requirement"
          >
            Copy link
          </button>
        </div>
        <img className="viewer-img" src={pageUrl(r.regulation, 'base', page, r.paragraph, page === r.page ? r.quote : '')} />
        {para && (
          <details style={{ marginTop: 10 }}>
            <summary className="small muted">Full paragraph text {para.label}</summary>
            <div className="small" style={{ marginTop: 6 }}>
              {para.text}
            </div>
          </details>
        )}
      </div>
    </>
  )
}

/* ------------------------------------------------------------------ screening ledger */
function Screening({ run, reqs }: { run: Any; reqs: Any[] }) {
  const [show, setShow] = useState<'relevant' | 'all'>('relevant')
  const counts: Record<string, number> = {}
  reqs.filter(r => r.exported).forEach(r => (counts[r.regulation] = (counts[r.regulation] || 0) + 1))
  const rows = (run.screening || []).filter((d: Any) => show === 'all' || d.decision !== 'not_applicable')
  const cls = (d: string) => (d === 'applicable' ? 'ok' : d === 'potentially_applicable' ? 'warn' : 'grey')
  return (
    <div className="card" style={{ padding: 0, overflow: 'hidden' }}>
      <div className="row" style={{ padding: '12px 16px' }}>
        <h2 style={{ margin: 0 }} className="grow">
          Applicability ledger · all {run.screening?.length || 0} regulations in the index
        </h2>
        <div className="pill-toggle">
          <button className={show === 'relevant' ? 'on' : ''} onClick={() => setShow('relevant')}>
            Applicable
          </button>
          <button className={show === 'all' ? 'on' : ''} onClick={() => setShow('all')}>
            All
          </button>
        </div>
      </div>
      <table className="tbl">
        <thead>
          <tr>
            <th>Document</th>
            <th>Decision</th>
            <th>Basis</th>
            <th style={{ width: '45%' }}>Reason</th>
            <th>Reqs</th>
          </tr>
        </thead>
        <tbody>
          {rows.map((d: Any) => (
            <tr key={d.regulation}>
              <td>
                <div className="doc-title">
                  {d.regulation} - {d.title}
                </div>
                <div className="doc-meta">
                  <span className="chip">
                    Version: <b>{d.version}</b>
                  </span>
                  <span className="chip">UNECE › UN-R</span>
                </div>
              </td>
              <td>
                <span className={`badge ${cls(d.decision)}`}>{d.decision.replace('_', ' ')}</span>
                <div className="small muted" style={{ marginTop: 4 }}>
                  p={d.probability.toFixed(2)}
                </div>
              </td>
              <td className="small">{d.basis.replace('_', ' ')}</td>
              <td className="small">{d.reason}</td>
              <td>{counts[d.regulation] ? <a href={`#/runs/${run.run_id}/requirements?reg=${encodeURIComponent(d.regulation)}`}>{counts[d.regulation]}</a> : '–'}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}

/* ------------------------------------------------------------------ coverage */
function Coverage({ run }: { run: Any }) {
  const cov: Any[] = run.coverage || []
  const byReg = new Map<string, Any[]>()
  cov.forEach(c => byReg.set(c.regulation, [...(byReg.get(c.regulation) || []), c]))
  const ev = run.eval
  return (
    <>
      <div className="grid3" style={{ marginBottom: 14 }}>
        <div className="card">
          <div className="stat-label">Sections processed</div>
          <div className="stat-value">
            {cov.filter(c => c.status === 'done').length} / {cov.length}
          </div>
          <div className="small muted">Processing statistic, not recall.</div>
        </div>
        <div className="card">
          <div className="stat-label">Paragraphs read</div>
          <div className="stat-value">{cov.reduce((a, c) => a + c.labels.length, 0)}</div>
        </div>
        <div className="card">
          <div className="stat-label">Requirements added by the audit</div>
          <div className="stat-value">{cov.reduce((a, c) => a + (c.n_audit || 0), 0)}</div>
        </div>
      </div>
      {ev?.local && (
        <div className="card">
          <h2>Benchmark on the worked example (evaluation, after the output was frozen)</h2>
          <table className="tbl">
            <thead>
              <tr>
                <th>Level</th>
                <th>Precision</th>
                <th>Recall</th>
                <th>Cited / expected / matched</th>
              </tr>
            </thead>
            <tbody>
              {Object.entries(ev.local).map(([k, v]: Any) => (
                <tr key={k}>
                  <td>{k.replace('_', ' ')} (official offline scorer)</td>
                  <td>{v.precision.toFixed(3)}</td>
                  <td>{v.recall.toFixed(3)}</td>
                  <td>
                    {v.n_submitted} / {v.n_expected} / {v.n_matched}
                  </td>
                </tr>
              ))}
              {ev.judge && (
                <tr>
                  <td>requirement level ({ev.judge.label})</td>
                  <td>{ev.judge.precision.toFixed(3)}</td>
                  <td>{ev.judge.recall.toFixed(3)}</td>
                  <td>
                    {ev.judge.n_submitted} / {ev.judge.n_expected} / {ev.judge.tp} · F2 {ev.judge.f2.toFixed(3)}
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      )}
      <div className="card">
        <h2>Section ledger</h2>
        {[...byReg.entries()].map(([reg, cs]) => (
          <div key={reg} style={{ marginBottom: 12 }}>
            <div className="doc-title" style={{ marginBottom: 4 }}>
              {reg}
            </div>
            <div className="row wrap" style={{ gap: 4 }}>
              {cs.map(c => (
                <span
                  key={String(c.chunk)}
                  className={`badge ${c.status === 'done' ? 'ok' : 'bad'}`}
                  title={`${c.labels[0]} … ${c.labels[c.labels.length - 1]}${c.error ? '\n' + c.error : ''}`}
                >
                  {c.labels[0]}–{c.labels[c.labels.length - 1]} · {c.n_requirements ?? 0}
                </span>
              ))}
            </div>
          </div>
        ))}
      </div>
    </>
  )
}

/* ------------------------------------------------------------------ export */
function Export({ run, reqs }: { run: Any; reqs: Any[] }) {
  const [thr, setThr] = useState<number>(run.inputs?.config?.threshold ?? 0.15)
  const [team, setTeam] = useState('')
  const [res, setRes] = useState<Any>(null)
  const n = reqs.filter(r => r.probability >= thr).length
  return (
    <div className="grid2" style={{ alignItems: 'start' }}>
      <div className="card">
        <h2>Main-goal submission</h2>
        <p className="muted small">
          Keep a candidate if the estimated probability that experts list it exceeds the threshold. F2 rewards recall: adding an item helps
          when its probability exceeds F2/5.
        </p>
        <div className="row" style={{ marginBottom: 10 }}>
          <span className="small" style={{ width: 90 }}>
            Threshold
          </span>
          <input type="range" min={0} max={0.9} step={0.05} value={thr} onChange={e => setThr(+e.target.value)} className="grow" />
          <b style={{ width: 40 }}>{thr.toFixed(2)}</b>
        </div>
        <div className="row" style={{ marginBottom: 10 }}>
          <span className="small" style={{ width: 90 }}>
            Team id
          </span>
          <input type="text" placeholder="from the platform (default: TEAM_ID in .env)" value={team} onChange={e => setTeam(e.target.value)}
            className="grow" />
        </div>
        <div className="row">
          <span className="grow">{n} requirements will be exported</span>
          <button className="btn" onClick={async () => setRes(await api.exportRun(run.run_id, { threshold: thr, team_id: team || undefined }))}>
            Export & validate
          </button>
          <a className="btn secondary" href={`/api/runs/${run.run_id}/submission.json`}>
            {I.export} Download
          </a>
        </div>
      </div>
      <div className="card">
        <h2>Validation</h2>
        {(res?.validation || run.validation) ? (
          <>
            <span className={`badge ${(res?.validation || run.validation).ok ? 'ok' : 'bad'}`}>
              {(res?.validation || run.validation).ok ? 'passes validate.py' : 'validation failed'}
            </span>
            <pre className="mono" style={{ whiteSpace: 'pre-wrap' }}>
              {(res?.validation || run.validation).output}
            </pre>
          </>
        ) : (
          <div className="muted">Not validated yet.</div>
        )}
      </div>
    </div>
  )
}
