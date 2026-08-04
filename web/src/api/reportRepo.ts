import type { Report } from '@/types/report'

const SESSION_KEY = 'hh-leads-session-id'

export function getSessionId(): string | null {
  return sessionStorage.getItem(SESSION_KEY)
}

export function setSessionId(id: string): void {
  sessionStorage.setItem(SESSION_KEY, id)
}

export function clearSessionId(): void {
  sessionStorage.removeItem(SESSION_KEY)
}

function headers(extra?: HeadersInit): Headers {
  const h = new Headers(extra)
  const sid = getSessionId()
  if (sid) h.set('X-Session-Id', sid)
  return h
}

async function readError(res: Response): Promise<string> {
  try {
    const data = await res.json()
    if (data?.detail) {
      return typeof data.detail === 'string' ? data.detail : JSON.stringify(data.detail)
    }
  } catch {
    /* ignore */
  }
  return res.statusText || `HTTP ${res.status}`
}

export async function fetchReport(): Promise<Report | null> {
  const sid = getSessionId()
  if (!sid) return null
  const res = await fetch('/api/report', { headers: headers() })
  if (res.status === 404) return null
  if (!res.ok) throw new Error(await readError(res))
  const data = await res.json()
  if (data.sessionId) setSessionId(data.sessionId)
  return data.report as Report
}

export async function syncReport(payload: {
  cookie: string
  days: number
  hhHost?: string
}): Promise<Report> {
  const res = await fetch('/api/sync', {
    method: 'POST',
    headers: headers({ 'Content-Type': 'application/json' }),
    body: JSON.stringify(payload),
  })
  if (!res.ok) throw new Error(await readError(res))
  const data = await res.json()
  if (data.sessionId) setSessionId(data.sessionId)
  return data.report as Report
}

export async function uploadReport(file: File): Promise<Report> {
  const form = new FormData()
  form.append('file', file)
  const res = await fetch('/api/upload', {
    method: 'POST',
    headers: headers(),
    body: form,
  })
  if (!res.ok) throw new Error(await readError(res))
  const data = await res.json()
  if (data.sessionId) setSessionId(data.sessionId)
  return data.report as Report
}

export async function clearServerSession(): Promise<void> {
  const sid = getSessionId()
  if (!sid) return
  await fetch('/api/session', { method: 'DELETE', headers: headers() })
  clearSessionId()
}
