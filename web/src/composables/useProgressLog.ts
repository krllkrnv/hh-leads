import { computed, type Reactive } from 'vue'
import type { ProgressEvent, ProgressStage } from '@/types/progress'

export type ProgressLogItem = {
  id: number
  stage: ProgressStage | 'info'
  message: string
  company?: string
  at: number
}

export type ProgressMode = 'sync' | 'upload' | null

type ProgressSlice = {
  progressStage: ProgressStage | null
  progressMessage: string
  progressCurrent: number
  progressTotal: number
  progressLogs: ProgressLogItem[]
  progressMode: ProgressMode
}

const MAX_LOGS = 120

/**
 * Лог и проценты прогресса sync/upload.
 */
export function useProgressLog(state: Reactive<ProgressSlice>) {
  let logSeq = 0

  const progressPercent = computed(() => {
    if (!state.progressTotal) {
      return 0
    }
    return Math.min(100, Math.round((state.progressCurrent / state.progressTotal) * 100))
  })

  function resetProgress(mode: ProgressMode): void {
    state.progressMode = mode
    state.progressStage = 'start'
    state.progressMessage =
      mode === 'upload' ? 'Готовлю разбор файла…' : 'Готовлю синхронизацию с hh…'
    state.progressCurrent = 0
    state.progressTotal = 0
    state.progressLogs = []
    logSeq = 0
  }

  function pushLog(event: ProgressEvent): void {
    const stage = event.stage || 'info'
    logSeq += 1
    state.progressLogs.push({
      id: logSeq,
      stage,
      message: event.message,
      company: event.company,
      at: Date.now(),
    })
    if (state.progressLogs.length > MAX_LOGS) {
      state.progressLogs.splice(0, state.progressLogs.length - MAX_LOGS)
    }
  }

  function handleProgressEvent(event: ProgressEvent): void {
    if (event.type === 'error') {
      pushLog({
        ...event,
        stage: 'error',
        message: event.message,
      })
      state.progressStage = 'error'
      state.progressMessage = event.message
      return
    }

    if (event.type === 'progress' || event.stage) {
      if (event.stage && event.stage !== 'warn') {
        state.progressStage = event.stage
      }
      if (event.message) {
        state.progressMessage = event.message
      }
      if (typeof event.current === 'number') {
        state.progressCurrent = event.current
      }
      if (typeof event.total === 'number') {
        state.progressTotal = event.total
      }
      pushLog(event)
    }

    if (event.type === 'done') {
      state.progressStage = 'done'
      state.progressMessage = event.message || 'Готово'
      if (state.progressTotal > 0) {
        state.progressCurrent = state.progressTotal
      }
      // Не пишем «Готово» второй раз, если такое сообщение уже есть в логе прогресса.
      const last = state.progressLogs[state.progressLogs.length - 1]
      if (!last || last.stage !== 'done') {
        pushLog({
          stage: 'done',
          message: event.message || 'Готово',
        })
      }
    }
  }

  function clearProgress(): void {
    state.progressMode = null
    state.progressLogs = []
    state.progressMessage = ''
    state.progressStage = null
  }

  return {
    progressPercent,
    resetProgress,
    handleProgressEvent,
    clearProgress,
  }
}
