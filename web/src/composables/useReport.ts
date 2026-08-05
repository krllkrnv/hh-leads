import { computed, reactive, watch } from 'vue'
import {
  cancelSync,
  clearServerSession,
  downloadReportExcel,
  ensureSessionId,
  fetchReport,
  humanizeError,
  syncReportStream,
  uploadReportStream,
} from '@/api/reportRepo'
import type { ProgressEvent, ProgressStage } from '@/types/progress'
import { matchesProfile } from '@/lib/leadDisplay'
import {
  DONE_STORAGE_KEY,
  EFilterKey,
  PREFS_STORAGE_KEY,
  type FilterKey,
  type Lead,
  type Report,
} from '@/types/report'

function loadDoneMap(): Record<string, boolean> {
  try {
    return JSON.parse(localStorage.getItem(DONE_STORAGE_KEY) || '{}') as Record<string, boolean>
  } catch {
    return {}
  }
}

type Prefs = {
  filter: FilterKey
  hideClosed: boolean
  includeKeywords: string
  excludeKeywords: string
}

function loadPrefs(): Prefs {
  const keys = new Set<string>(Object.values(EFilterKey))
  try {
    const raw = JSON.parse(localStorage.getItem(PREFS_STORAGE_KEY) || '{}') as Partial<Prefs>
    const filter = keys.has(String(raw.filter)) ? (raw.filter as FilterKey) : EFilterKey.All
    return {
      filter,
      hideClosed: raw.hideClosed ?? true,
      includeKeywords: raw.includeKeywords ?? '',
      excludeKeywords: raw.excludeKeywords ?? '',
    }
  } catch {
    return {
      filter: EFilterKey.All,
      hideClosed: true,
      includeKeywords: '',
      excludeKeywords: '',
    }
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
  includeKeywords: string
  excludeKeywords: string
  showSetup: boolean
  doneMap: Record<string, boolean>
  progressStage: ProgressStage | null
  progressMessage: string
  progressCurrent: number
  progressTotal: number
  progressLogs: ProgressLogItem[]
  progressMode: 'sync' | 'upload' | null
}

type FilterCounts = Record<FilterKey, number>

const EMPTY_COUNTS: FilterCounts = {
  [EFilterKey.All]: 0,
  [EFilterKey.Reply]: 0,
  [EFilterKey.Call]: 0,
  [EFilterKey.Interview]: 0,
  [EFilterKey.Test]: 0,
  [EFilterKey.Invites]: 0,
  [EFilterKey.Wait]: 0,
  [EFilterKey.Bot]: 0,
  [EFilterKey.Closed]: 0,
}

const MAX_LOGS = 120

/**
 * Состояние дашборда: синхронизация и загрузка файла, фильтры очередей,
 * локальные отметки «разобрано» в браузере.
 */
export function useReport() {
  const prefs = loadPrefs()
  const state = reactive<ReportState>({
    report: null,
    loading: false,
    error: '',
    filter: prefs.filter,
    query: '',
    hideClosed: prefs.hideClosed,
    includeKeywords: prefs.includeKeywords,
    excludeKeywords: prefs.excludeKeywords,
    showSetup: false,
    doneMap: loadDoneMap(),
    progressStage: null,
    progressMessage: '',
    progressCurrent: 0,
    progressTotal: 0,
    progressLogs: [],
    progressMode: null,
  })

  let logSeq = 0
  let abortController: AbortController | null = null

  watch(
    () => [state.filter, state.hideClosed, state.includeKeywords, state.excludeKeywords] as const,
    ([filter, hideClosed, includeKeywords, excludeKeywords]) => {
      localStorage.setItem(
        PREFS_STORAGE_KEY,
        JSON.stringify({
          filter,
          hideClosed,
          includeKeywords,
          excludeKeywords,
        } satisfies Prefs),
      )
    },
  )

  const meta = computed(() => state.report?.meta ?? null)

  const progressPercent = computed(() => {
    if (!state.progressTotal) {
      return 0
    }
    return Math.min(100, Math.round((state.progressCurrent / state.progressTotal) * 100))
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
      [EFilterKey.Wait]: leads.wait?.length ?? 0,
      [EFilterKey.Bot]: leads.bot?.length ?? 0,
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
      [EFilterKey.Wait]: leads.wait ?? [],
      [EFilterKey.Bot]: leads.bot ?? [],
      [EFilterKey.Closed]: leads.closed,
    }

    const list = byFilter[state.filter] ?? leads.all
    const q = state.query.trim().toLowerCase()

    return list.filter((lead) => {
      if (
        state.hideClosed &&
        state.filter !== EFilterKey.Closed &&
        (lead.closed || lead.tag === 'closed')
      ) {
        return false
      }
      if (!matchesProfile(lead, state.includeKeywords, state.excludeKeywords)) {
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
    state.progressMessage = mode === 'upload' ? 'Готовлю разбор файла…' : 'Готовлю синхронизацию с hh…'
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

  /**
   * Убирает из локальных отметок «разобрано» id, которых больше нет в новом отчёте.
   */
  function pruneDoneMap(report: Report): void {
    const ids = new Set(report.leads.all.map((lead) => lead.id))
    const next: Record<string, boolean> = {}
    for (const [id, value] of Object.entries(state.doneMap)) {
      if (ids.has(id) && value) {
        next[id] = true
      }
    }
    state.doneMap = next
    localStorage.setItem(DONE_STORAGE_KEY, JSON.stringify(state.doneMap))
  }

  /**
   * Запоминает в localStorage, отмечен ли лид как разобранный.
   */
  function setDone(id: string, value: boolean): void {
    state.doneMap = { ...state.doneMap, [id]: value }
    localStorage.setItem(DONE_STORAGE_KEY, JSON.stringify(state.doneMap))
  }

  function isDone(id: string): boolean {
    return Boolean(state.doneMap[id])
  }

  /**
   * Тихо подтягивает сохранённый отчёт сессии при открытии страницы, без панели прогресса.
   */
  async function bootstrap(): Promise<void> {
    state.error = ''
    try {
      const report = await fetchReport()
      state.report = report
      if (report) {
        pruneDoneMap(report)
      }
    } catch (err) {
      state.error = humanizeError(err instanceof Error ? err.message : String(err))
    }
  }

  async function runSync(cookie: string, days: number, hhHost?: string): Promise<void> {
    state.loading = true
    state.error = ''
    resetProgress('sync')
    ensureSessionId()
    abortController = new AbortController()
    try {
      const report = await syncReportStream(
        {
          cookie,
          days,
          hhHost: hhHost || undefined,
        },
        handleProgressEvent,
        abortController.signal,
      )
      state.report = report
      pruneDoneMap(report)
      state.showSetup = false
    } catch (err) {
      if (abortController?.signal.aborted) {
        state.error =
          'Синхронизацию остановили. Уже разобранные чаты могли сохраниться как частичный отчёт.'
      } else {
        const status = (err as Error & { status?: number }).status
        const raw = err instanceof Error ? err.message : String(err)
        if (status === 401) {
          state.error =
            'Сессия hh больше не действует. Скопируйте cookie из браузера заново и загрузите чаты ещё раз.'
        } else {
          state.error = humanizeError(raw)
        }
      }
    } finally {
      state.loading = false
      abortController = null
    }
  }

  async function runUpload(file: File): Promise<void> {
    state.loading = true
    state.error = ''
    resetProgress('upload')
    ensureSessionId()
    abortController = new AbortController()
    try {
      const report = await uploadReportStream(file, handleProgressEvent, abortController.signal)
      state.report = report
      pruneDoneMap(report)
      state.showSetup = false
    } catch (err) {
      if (abortController?.signal.aborted) {
        state.error = 'Разбор файла остановили.'
      } else {
        const raw = err instanceof Error ? err.message : String(err)
        state.error = humanizeError(raw)
      }
    } finally {
      state.loading = false
      abortController = null
    }
  }

  async function cancelJob(): Promise<void> {
    abortController?.abort()
    await cancelSync()
    state.progressMessage = 'Останавливаю текущую загрузку…'
  }

  /**
   * Скачивает текущий отчёт: JSON в браузере или Excel с сервера.
   */
  async function exportReport(format: 'json' | 'xlsx' = 'json'): Promise<void> {
    if (!state.report) {
      return
    }
    const stamp = state.report.meta.exportedAt.replace(/[^\d]/g, '').slice(0, 12) || 'report'

    if (format === 'json') {
      const blob = new Blob([JSON.stringify(state.report, null, 2)], {
        type: 'application/json',
      })
      const url = URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = `hh-leads-${stamp}.json`
      a.click()
      URL.revokeObjectURL(url)
      return
    }

    try {
      const { blob, filename } = await downloadReportExcel()
      const url = URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = filename || `hh-leads-${stamp}.xlsx`
      a.click()
      URL.revokeObjectURL(url)
    } catch (err) {
      state.error = humanizeError(err instanceof Error ? err.message : String(err))
    }
  }

  function openSetup(): void {
    state.showSetup = true
    state.error = ''
  }

  function closeSetup(): void {
    state.showSetup = false
  }

  async function reset(): Promise<void> {
    await clearServerSession()
    state.report = null
    state.error = ''
    state.showSetup = false
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
    cancelJob,
    exportReport,
    openSetup,
    closeSetup,
    reset,
  }
}
