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
  { id: 'auth', label: 'Проверка cookie' },
  { id: 'list', label: 'Список чатов' },
  { id: 'fetch', label: 'Переписки' },
  { id: 'classify', label: 'Разбор лидов' },
  { id: 'parse', label: 'Чтение файла' },
  { id: 'build', label: 'Сборка отчёта' },
]
