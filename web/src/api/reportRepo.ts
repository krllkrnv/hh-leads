import type { Report } from '@/types/report'
import type { ProgressEvent } from '@/types/progress'
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
 * Гарантирует наличие session id до старта job (для cancel).
 */
export function ensureSessionId(): string {
  const existing = getSessionId()
  if (existing) {
    return existing
  }
  const id = crypto.randomUUID().replace(/-/g, '') + secretsToken()
  setSessionId(id)
  return id
}

function secretsToken(): string {
  const bytes = new Uint8Array(8)
  crypto.getRandomValues(bytes)
  return Array.from(bytes, (b) => b.toString(16).padStart(2, '0')).join('')
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
 * Читает NDJSON-стрим и вызывает onEvent на каждое событие.
 */
async function readNdjsonStream(
  res: Response,
  onEvent: (event: ProgressEvent) => void,
): Promise<Report> {
  if (!res.ok || !res.body) {
    throw new Error(await readError(res))
  }

  const reader = res.body.getReader()
  const decoder = new TextDecoder()
  let buffer = ''
  let report: Report | null = null
  let streamError: string | null = null

  try {
    while (true) {
      const { done, value } = await reader.read()
      if (done) {
        break
      }
      buffer += decoder.decode(value, { stream: true })
      const lines = buffer.split('\n')
      buffer = lines.pop() || ''

      for (const line of lines) {
        const trimmed = line.trim()
        if (!trimmed) {
          continue
        }
        let event: ProgressEvent
        try {
          event = JSON.parse(trimmed) as ProgressEvent
        } catch {
          continue
        }
        if (event.sessionId) {
          setSessionId(event.sessionId)
        }
        onEvent(event)
        if (event.type === 'done' && event.report) {
          report = event.report
        }
        if (event.type === 'error') {
          streamError = event.message || 'Ошибка синхронизации'
        }
      }
    }
  } catch (err) {
    if (err instanceof DOMException && err.name === 'AbortError') {
      throw err
    }
    throw err
  }

  if (buffer.trim()) {
    try {
      const event = JSON.parse(buffer.trim()) as ProgressEvent
      if (event.sessionId) {
        setSessionId(event.sessionId)
      }
      onEvent(event)
      if (event.type === 'done' && event.report) {
        report = event.report
      }
      if (event.type === 'error') {
        streamError = event.message || 'Ошибка синхронизации'
      }
    } catch {
      /* ignore trailing junk */
    }
  }

  if (streamError) {
    throw new Error(streamError)
  }
  if (!report) {
    throw new Error('Стрим завершился без отчёта')
  }
  return report
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
 * Синхронизирует чаты со стримом прогресса.
 */
export async function syncReportStream(
  payload: SyncPayload,
  onEvent: (event: ProgressEvent) => void,
  signal?: AbortSignal,
): Promise<Report> {
  const res = await fetch('/api/sync/stream', {
    method: 'POST',
    headers: headers({ 'Content-Type': 'application/json' }),
    body: JSON.stringify(payload),
    signal,
  })
  return readNdjsonStream(res, onEvent)
}

/**
 * Загружает файл со стримом прогресса.
 */
export async function uploadReportStream(
  file: File,
  onEvent: (event: ProgressEvent) => void,
  signal?: AbortSignal,
): Promise<Report> {
  const form = new FormData()
  form.append('file', file)
  const res = await fetch('/api/upload/stream', {
    method: 'POST',
    headers: headers(),
    body: form,
    signal,
  })
  return readNdjsonStream(res, onEvent)
}

/**
 * Просит сервер остановить текущую синхронизацию.
 */
export async function cancelSync(): Promise<void> {
  const sid = getSessionId()
  if (!sid) {
    return
  }
  await fetch('/api/sync/cancel', {
    method: 'POST',
    headers: headers(),
  }).catch(() => undefined)
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
