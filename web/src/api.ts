/* eslint-disable @typescript-eslint/no-explicit-any */
export type Any = any

async function j(url: string, init?: RequestInit) {
  const r = await fetch(url, init)
  if (!r.ok) throw new Error(`${r.status} ${await r.text()}`)
  return r.json()
}

export const api = {
  cases: () => j('/api/cases'),
  caseInputs: (id: string) => j(`/api/cases/${id}/inputs`),
  runs: () => j('/api/runs'),
  run: (id: string) => j(`/api/runs/${id}`),
  requirements: (id: string) => j(`/api/runs/${id}/requirements`),
  startRun: (body: Any) => j('/api/runs', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(body) }),
  startUpload: (fd: FormData) => j('/api/runs/upload', { method: 'POST', body: fd }),
  exportRun: (id: string, body: Any) =>
    j(`/api/runs/${id}/export`, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(body) }),
  review: (id: string, body: Any) =>
    j(`/api/runs/${id}/review`, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(body) }),
  reviews: (id: string) => j(`/api/runs/${id}/reviews`),
  regulations: () => j('/api/regulations'),
  outline: (reg: string, role: string) => j(`/api/doc/${encodeURIComponent(reg)}/${role}/outline`),
  docMeta: (reg: string, role: string) => j(`/api/doc/${encodeURIComponent(reg)}/${role}/meta`),
  paragraph: (reg: string, role: string, label: string) =>
    j(`/api/doc/${encodeURIComponent(reg)}/${role}/paragraph?label=${encodeURIComponent(label)}`),
  subgoals: () => j('/api/subgoal'),
  subgoal: (id: string) => j(`/api/subgoal/${id}`),
  startSubgoal: (body: Any) =>
    j('/api/subgoal', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(body) }),
  usage: () => j('/api/usage'),
}

export const pageUrl = (reg: string, role: string, page: number, label = '', q = '') =>
  `/api/doc/${encodeURIComponent(reg)}/${role}/page/${page}.png?label=${encodeURIComponent(label)}&q=${encodeURIComponent(q)}`
export const pdfUrl = (reg: string, role: string, page = 1) => `/api/doc/${encodeURIComponent(reg)}/${role}/pdf#page=${page}`
