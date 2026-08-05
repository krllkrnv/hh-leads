import type { Report } from '@/types/report'
import type { ProgressEvent } from '@/types/progress'
import { SESSION_STORAGE_KEY } from '@/types/report'

/**
 * Возвращает id серверной сессии из sessionStorage браузера.
 */
export function getSessionId(): string | null {
  return sessionStorage.getItem(SESSION_STORAGE_KEY)
}

/**
 * Сохраняет id серверной сессии в sessionStorage.
 * @param id - идентификатор сессии на API
 */
export function setSessionId(id: string): void {
  sessionStorage.setItem(SESSION_STORAGE_KEY, id)
}

/**
 * Гарантирует, что session id уже есть до старта синхронизации —
 * иначе кнопка «Остановить» не сможет сказать серверу, какую задачу отменить.
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
 * Удаляет id серверной сессии из sessionStorage.
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
      const detail = typeof data.detail === 'string' ? data.detail : JSON.stringify(data.detail)
      return humanizeError(detail)
    }
  } catch {
    /* ignore non-json */
  }
  if (res.status === 401) {
    return 'Сессия hh больше не действует. Скопируйте cookie из браузера заново.'
  }
  if (res.status === 413) {
    return 'Файл слишком большой. Максимум 15 МБ.'
  }
  if (res.status >= 500) {
    return 'Сервер не смог обработать запрос. Попробуйте ещё раз.'
  }
  return 'Не удалось выполнить запрос. Попробуйте ещё раз.'
}

/**
 * Переводит технические тексты ошибок в короткие понятные сообщения.
 */
export function humanizeError(raw: string): string {
  const text = raw.trim()
  if (!text) {
    return 'Что-то пошло не так. Попробуйте ещё раз.'
  }
  if (/сессия|cookie|недействительн|auth|401/i.test(text)) {
    return 'Сессия hh больше не действует. Скопируйте cookie из браузера заново и загрузите чаты ещё раз.'
  }
  if (/429|temporary|502|503|504|network|не отвечает/i.test(text)) {
    return 'hh сейчас не отвечает. Подождите немного и попробуйте снова.'
  }
  if (/отмен|остановил/i.test(text)) {
    return text
  }
  // Уже нормальный русский текст от нашего API — показываем как есть.
  if (/[а-яё]/i.test(text) && !/Chatik|Traceback|HTTP \d|Sync failed|NDJSON|stack/i.test(text)) {
    return text.length > 220 ? `${text.slice(0, 217)}…` : text
  }
  return 'Не удалось загрузить данные. Проверьте cookie и попробуйте ещё раз.'
}

/**
 * Читает поток прогресса в формате NDJSON и вызывает onEvent на каждое событие.
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
  let streamStatus: number | undefined

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
          streamError = event.message || 'Не удалось завершить синхронизацию'
          streamStatus = event.status
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
        streamError = event.message || 'Не удалось завершить синхронизацию'
        streamStatus = event.status
      }
    } catch {
      /* trailing junk */
    }
  }

  if (streamError) {
    const err = new Error(humanizeError(streamError)) as Error & { status?: number }
    err.status = streamStatus
    throw err
  }
  if (!report) {
    throw new Error('Не удалось получить отчёт. Попробуйте загрузить чаты ещё раз.')
  }
  return report
}

/**
 * Загружает текущий отчёт сессии с сервера. Без session id возвращает null.
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
 * Синхронизирует чаты с hh и стримит прогресс в onEvent.
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
 * Загружает файл отчёта и стримит прогресс разбора в onEvent.
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
 * Скачивает Excel-отчёт текущей сессии с сервера.
 */
export async function downloadReportExcel(): Promise<{ blob: Blob; filename: string }> {
  const res = await fetch('/api/report/excel', { headers: headers() })
  if (!res.ok) {
    throw new Error(await readError(res))
  }
  const blob = await res.blob()
  const disposition = res.headers.get('Content-Disposition') || ''
  const match = disposition.match(/filename="?([^";]+)"?/i)
  const filename = match?.[1] || `hh-leads-${Date.now()}.xlsx`
  return { blob, filename }
}

/**
 * Просит сервер остановить текущую синхронизацию для этой сессии.
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
 * Удаляет отчёт на сервере и забывает локальный session id.
 */
export async function clearServerSession(): Promise<void> {
  const sid = getSessionId()
  if (!sid) {
    return
  }
  await fetch('/api/session', { method: 'DELETE', headers: headers() })
  clearSessionId()
}
