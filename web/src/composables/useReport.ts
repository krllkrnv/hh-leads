import { computed, reactive } from 'vue'
import {
  clearServerSession,
  fetchReport,
  syncReportStream,
  uploadReportStream,
} from '@/api/reportRepo'
import type { ProgressEvent, ProgressStage } from '@/types/progress'
import { isFrontendLead } from '@/lib/leadDisplay'
import {
  DONE_STORAGE_KEY,
  EFilterKey,
  type FilterKey,
  type Lead,
  type Report,
} from '@/types/report'

function loadDoneMap(): Record<string, boolean> {
  try {
    return JSON.parse(localStorage.getItem(DONE_STORAGE_KEY) || '{}') as Record<
      string,
      boolean
    >
  } catch {
    return {}
  }
}

type ProgressLogItem = {
  id: number
  stage: ProgressStage | 'info'
  message: string
  company?: string
  at: number
}

type ReportState = {
  report: Report | null
  loading: boolean
  error: string
  filter: FilterKey
  query: string
  hideClosed: boolean
  frontendOnly: boolean
  doneMap: Record<string, boolean>
  progressStage: ProgressStage | null
  progressMessage: string
  progressCurrent: number
  progressTotal: number
  progressLogs: ProgressLogItem[]
  progressMode: 'sync' | 'upload' | 'boot' | null
}

type FilterCounts = Record<FilterKey, number>

const EMPTY_COUNTS: FilterCounts = {
  [EFilterKey.All]: 0,
  [EFilterKey.Reply]: 0,
  [EFilterKey.Call]: 0,
  [EFilterKey.Interview]: 0,
  [EFilterKey.Test]: 0,
  [EFilterKey.Invites]: 0,
  [EFilterKey.Closed]: 0,
}

const MAX_LOGS = 120

/**
 * Состояние отчёта: sync/upload, фильтры очередей, локальные «сделано».
 */
export function useReport() {
  const state = reactive<ReportState>({
    report: null,
    loading: false,
    error: '',
    filter: EFilterKey.All,
    query: '',
    hideClosed: true,
    frontendOnly: false,
    doneMap: loadDoneMap(),
    progressStage: null,
    progressMessage: '',
    progressCurrent: 0,
    progressTotal: 0,
    progressLogs: [],
    progressMode: null,
  })

  let logSeq = 0

  const meta = computed(() => state.report?.meta ?? null)

  const progressPercent = computed(() => {
    if (!state.progressTotal) {
      return 0
    }
    return Math.min(
      100,
      Math.round((state.progressCurrent / state.progressTotal) * 100),
    )
  })

  const filterCounts = computed<FilterCounts>(() => {
    const leads = state.report?.leads
    if (!leads) {
      return { ...EMPTY_COUNTS }
    }
    return {
      [EFilterKey.All]: leads.all.length,
      [EFilterKey.Reply]: leads.reply.length,
      [EFilterKey.Call]: leads.contact.length,
      [EFilterKey.Interview]: leads.interview.length,
      [EFilterKey.Test]: leads.tests.length,
      [EFilterKey.Invites]: leads.invites.length,
      [EFilterKey.Closed]: leads.closed.length,
    }
  })

  const visibleLeads = computed<Lead[]>(() => {
    const leads = state.report?.leads
    if (!leads) {
      return []
    }

    const byFilter: Record<FilterKey, Lead[]> = {
      [EFilterKey.All]: leads.all,
      [EFilterKey.Reply]: leads.reply,
      [EFilterKey.Call]: leads.contact,
      [EFilterKey.Interview]: leads.interview,
      [EFilterKey.Test]: leads.tests,
      [EFilterKey.Invites]: leads.invites,
      [EFilterKey.Closed]: leads.closed,
    }

    const list = byFilter[state.filter] ?? leads.all
    const q = state.query.trim().toLowerCase()

    return list.filter((lead) => {
      if (
        state.hideClosed
        && state.filter !== EFilterKey.Closed
        && (lead.closed || lead.tag === 'closed')
      ) {
        return false
      }
      if (state.frontendOnly && !isFrontendLead(lead)) {
        return false
      }
      if (!q) {
        return true
      }
      const hay = `${lead.company} ${lead.vacancy} ${lead.why} ${lead.status}`.toLowerCase()
      return hay.includes(q)
    })
  })

  function resetProgress(mode: ReportState['progressMode']): void {
    state.progressMode = mode
    state.progressStage = 'start'
    state.progressMessage = mode === 'upload' ? 'Готовлю загрузку файла…' : 'Готовлю синхронизацию…'
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
      pushLog({
        stage: 'done',
        message: event.message || 'Готово',
      })
    }
  }

  /**
   * Сохраняет чекбокс «сделано» в localStorage.
   */
  function setDone(id: string, value: boolean): void {
    state.doneMap = { ...state.doneMap, [id]: value }
    localStorage.setItem(DONE_STORAGE_KEY, JSON.stringify(state.doneMap))
  }

  function isDone(id: string): boolean {
    return Boolean(state.doneMap[id])
  }

  async function bootstrap(): Promise<void> {
    state.loading = true
    state.error = ''
    state.progressMode = 'boot'
    state.progressMessage = 'Проверяю сохранённую сессию…'
    try {
      state.report = await fetchReport()
    } catch (err) {
      state.error = err instanceof Error ? err.message : String(err)
    } finally {
      state.loading = false
      state.progressMode = null
      state.progressMessage = ''
    }
  }

  async function runSync(cookie: string, days: number, hhHost?: string): Promise<void> {
    state.loading = true
    state.error = ''
    resetProgress('sync')
    try {
      state.report = await syncReportStream(
        {
          cookie,
          days,
          hhHost: hhHost || undefined,
        },
        handleProgressEvent,
      )
    } catch (err) {
      state.error = err instanceof Error ? err.message : String(err)
      throw err
    } finally {
      state.loading = false
    }
  }

  async function runUpload(file: File): Promise<void> {
    state.loading = true
    state.error = ''
    resetProgress('upload')
    try {
      state.report = await uploadReportStream(file, handleProgressEvent)
    } catch (err) {
      state.error = err instanceof Error ? err.message : String(err)
      throw err
    } finally {
      state.loading = false
    }
  }

  async function reset(): Promise<void> {
    await clearServerSession()
    state.report = null
    state.error = ''
    state.progressMode = null
    state.progressLogs = []
    state.progressMessage = ''
    state.progressStage = null
  }

  return {
    state,
    meta,
    filterCounts,
    visibleLeads,
    progressPercent,
    setDone,
    isDone,
    bootstrap,
    runSync,
    runUpload,
    reset,
  }
}
