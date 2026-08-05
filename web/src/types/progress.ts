export type ProgressStage =
  'start' | 'auth' | 'list' | 'fetch' | 'classify' | 'parse' | 'build' | 'done' | 'error' | 'warn'

export type ProgressEvent = {
  type?: 'progress' | 'done' | 'error'
  stage?: ProgressStage
  message: string
  current?: number
  total?: number
  company?: string
  detail?: string
  sessionId?: string
  status?: number
  report?: import('./report').Report
}

export const PROGRESS_STAGES: Array<{
  id: ProgressStage
  label: string
}> = [
  { id: 'auth', label: 'Сессия' },
  { id: 'list', label: 'Список чатов' },
  { id: 'fetch', label: 'Переписки' },
  { id: 'classify', label: 'Классификация' },
  { id: 'parse', label: 'Разбор файла' },
  { id: 'build', label: 'Отчёт' },
]
