import type { Report } from '@/types/report'
import { SESSION_STORAGE_KEY } from '@/types/report'

/**
 * Возвращает id серверной сессии из sessionStorage.
 */
export function getSessionId(): string | null {
  return sessionStorage.getItem(SESSION_STORAGE_KEY)
}

/**
 * Сохраняет id серверной сессии.
 * @param id - идентификатор сессии
 */
export function setSessionId(id: string): void {
  sessionStorage.setItem(SESSION_STORAGE_KEY, id)
}

/**
 * Удаляет id серверной сессии.
 */
export function clearSessionId(): void {
  sessionStorage.removeItem(SESSION_STORAGE_KEY)
}

function headers(extra?: HeadersInit): Headers {
  const h = new Headers(extra)
  const sid = getSessionId()
  if (sid) {
    h.set('X-Session-Id', sid)
  }
  return h
}

async function readError(res: Response): Promise<string> {
  try {
    const data: { detail?: string | unknown } = await res.json()
    if (data?.detail) {
      return typeof data.detail === 'string' ? data.detail : JSON.stringify(data.detail)
    }
  } catch {
    /* ignore non-json */
  }
  return res.statusText || `HTTP ${res.status}`
}

/**
 * Загружает текущий отчёт сессии. Без session id возвращает null.
 */
export async function fetchReport(): Promise<Report | null> {
  const sid = getSessionId()
  if (!sid) {
    return null
  }

  const res = await fetch('/api/report', { headers: headers() })
  if (res.status === 404) {
    return null
  }
  if (!res.ok) {
    throw new Error(await readError(res))
  }

  const data: { sessionId?: string; report: Report } = await res.json()
  if (data.sessionId) {
    setSessionId(data.sessionId)
  }
  return data.report
}

type SyncPayload = {
  cookie: string
  days: number
  hhHost?: string
}

/**
 * Синхронизирует чаты через Chatik API.
 * @param payload - cookie, период и опциональный host
 */
export async function syncReport(payload: SyncPayload): Promise<Report> {
  const res = await fetch('/api/sync', {
    method: 'POST',
    headers: headers({ 'Content-Type': 'application/json' }),
    body: JSON.stringify(payload),
  })
  if (!res.ok) {
    throw new Error(await readError(res))
  }

  const data: { sessionId?: string; report: Report } = await res.json()
  if (data.sessionId) {
    setSessionId(data.sessionId)
  }
  return data.report
}

/**
 * Загружает xlsx/json отчёт на сервер.
 * @param file - файл выгрузки
 */
export async function uploadReport(file: File): Promise<Report> {
  const form = new FormData()
  form.append('file', file)
  const res = await fetch('/api/upload', {
    method: 'POST',
    headers: headers(),
    body: form,
  })
  if (!res.ok) {
    throw new Error(await readError(res))
  }

  const data: { sessionId?: string; report: Report } = await res.json()
  if (data.sessionId) {
    setSessionId(data.sessionId)
  }
  return data.report
}

/**
 * Очищает серверную сессию и локальный session id.
 */
export async function clearServerSession(): Promise<void> {
  const sid = getSessionId()
  if (!sid) {
    return
  }
  await fetch('/api/session', { method: 'DELETE', headers: headers() })
  clearSessionId()
}
