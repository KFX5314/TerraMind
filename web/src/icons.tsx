const s = { fill: 'none', stroke: 'currentColor', strokeWidth: 1.7, strokeLinecap: 'round' as const, strokeLinejoin: 'round' as const }

export const I = {
  search: <svg viewBox="0 0 24 24" {...s}><circle cx="11" cy="11" r="7" /><path d="m20 20-3.5-3.5" /></svg>,
  projects: <svg viewBox="0 0 24 24" {...s}><rect x="4" y="3" width="13" height="16" rx="2" /><path d="M8 7h6M8 11h6M8 15h3M20 7v13a1 1 0 0 1-1 1H8" /></svg>,
  doc: <svg viewBox="0 0 24 24" {...s}><path d="M14 3H7a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h10a2 2 0 0 0 2-2V8z" /><path d="M14 3v5h5" /></svg>,
  check: <svg viewBox="0 0 24 24" {...s}><circle cx="12" cy="12" r="9" /><path d="m8 12 3 3 5-6" /></svg>,
  list: <svg viewBox="0 0 24 24" {...s}><path d="M8 6h13M8 12h13M8 18h13M3 6h.01M3 12h.01M3 18h.01" /></svg>,
  browse: <svg viewBox="0 0 24 24" {...s}><path d="M4 6h16M4 12h16M4 18h16" /></svg>,
  changes: <svg viewBox="0 0 24 24" {...s}><path d="M4 7h11l-3-3M20 17H9l3 3" /></svg>,
  export: <svg viewBox="0 0 24 24" {...s}><path d="M12 3v12M7 8l5-5 5 5M5 21h14" /></svg>,
  layers: <svg viewBox="0 0 24 24" {...s}><path d="m12 3 9 5-9 5-9-5 9-5Z" /><path d="m3 13 9 5 9-5" /></svg>,
  cpu: <svg viewBox="0 0 24 24" {...s}><rect x="6" y="6" width="12" height="12" rx="2" /><path d="M9 2v4M15 2v4M9 18v4M15 18v4M2 9h4M2 15h4M18 9h4M18 15h4" /></svg>,
  coin: <svg viewBox="0 0 24 24" {...s}><circle cx="12" cy="12" r="9" /><path d="M14.5 9a2.5 2.5 0 0 0-2.5-1.5c-1.4 0-2.5.7-2.5 2s1.1 1.7 2.5 2 2.5.7 2.5 2-1.1 2-2.5 2a2.6 2.6 0 0 1-2.5-1.5M12 6v1.5M12 16.5V18" /></svg>,
  page: <svg viewBox="0 0 24 24" {...s}><rect x="5" y="3" width="14" height="18" rx="2" /><path d="M9 8h6M9 12h6M9 16h4" /></svg>,
  ext: <svg viewBox="0 0 24 24" {...s}><path d="M14 4h6v6M20 4l-9 9M19 14v5a1 1 0 0 1-1 1H5a1 1 0 0 1-1-1V6a1 1 0 0 1 1-1h5" /></svg>,
  star: <svg viewBox="0 0 24 24" fill="currentColor"><path d="m12 3 2.7 5.6 6.1.9-4.4 4.3 1 6.1L12 17l-5.4 2.9 1-6.1L3.2 9.5l6.1-.9z" /></svg>,
}
