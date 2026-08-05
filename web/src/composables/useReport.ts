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
import { downloadBlob } from '@/lib/downloadBlob'
import { countByFilter, getLeadsForFilter } from '@/lib/leadBuckets'
import { matchesProfile } from '@/lib/leadDisplay'
import {
  useProgressLog,
  type ProgressLogItem,
  type ProgressMode,
} from '@/composables/useProgressLog'
import {
  loadDoneMap,
  loadPrefs,
  pruneDoneMap,
  saveDoneMap,
  savePrefs,
  type ReportPrefs,
} from '@/composables/useReportPrefs'
import {
  EFilterKey,
  type FilterKey,
  type Lead,
  type Report,
} from '@/types/report'

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
  progressMode: ProgressMode
}

/**
 * Состояние дашборда: синхронизация и загрузка файла, фильтры лидов,
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

  const { progressPercent, resetProgress, handleProgressEvent, clearProgress } =
    useProgressLog(state)

  let abortController: AbortController | null = null

  watch(
    () => [state.filter, state.hideClosed, state.includeKeywords, state.excludeKeywords] as const,
    ([filter, hideClosed, includeKeywords, excludeKeywords]) => {
      savePrefs({
        filter,
        hideClosed,
        includeKeywords,
        excludeKeywords,
      } satisfies ReportPrefs)
    },
  )

  const meta = computed(() => state.report?.meta ?? null)

  const filterCounts = computed(() => countByFilter(state.report))

  const visibleLeads = computed<Lead[]>(() => {
    const list = getLeadsForFilter(state.report, state.filter)
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

  function applyReport(report: Report): void {
    state.report = report
    state.doneMap = pruneDoneMap(state.doneMap, report)
    saveDoneMap(state.doneMap)
    state.showSetup = false
  }

  function setDone(id: string, value: boolean): void {
    state.doneMap = { ...state.doneMap, [id]: value }
    saveDoneMap(state.doneMap)
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
      if (report) {
        state.report = report
        state.doneMap = pruneDoneMap(state.doneMap, report)
        saveDoneMap(state.doneMap)
      } else {
        state.report = null
      }
    } catch (err) {
      state.error = humanizeError(err instanceof Error ? err.message : String(err))
    }
  }

  async function runJob(
    mode: 'sync' | 'upload',
    task: (signal: AbortSignal, onProgress: (event: ProgressEvent) => void) => Promise<Report>,
    messages: { aborted: string; mapError?: (err: unknown) => string | null },
  ): Promise<void> {
    state.loading = true
    state.error = ''
    resetProgress(mode)
    ensureSessionId()
    abortController = new AbortController()
    try {
      const report = await task(abortController.signal, handleProgressEvent)
      applyReport(report)
    } catch (err) {
      if (abortController?.signal.aborted) {
        state.error = messages.aborted
      } else {
        const mapped = messages.mapError?.(err)
        if (mapped) {
          state.error = mapped
        } else {
          const raw = err instanceof Error ? err.message : String(err)
          state.error = humanizeError(raw)
        }
      }
    } finally {
      state.loading = false
      abortController = null
    }
  }

  async function runSync(cookie: string, days: number, hhHost?: string): Promise<void> {
    await runJob(
      'sync',
      (signal, onProgress) =>
        syncReportStream(
          {
            cookie,
            days,
            hhHost: hhHost || undefined,
          },
          onProgress,
          signal,
        ),
      {
        aborted:
          'Синхронизацию остановили. Уже разобранные чаты могли сохраниться как частичный отчёт.',
        mapError: (err) => {
          const status = (err as Error & { status?: number }).status
          if (status === 401) {
            return 'Сессия hh больше не действует. Скопируйте cookie из браузера заново и загрузите чаты ещё раз.'
          }
          return null
        },
      },
    )
  }

  async function runUpload(file: File): Promise<void> {
    await runJob(
      'upload',
      (signal, onProgress) => uploadReportStream(file, onProgress, signal),
      { aborted: 'Разбор файла остановили.' },
    )
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
      downloadBlob(blob, `hh-leads-${stamp}.json`)
      return
    }

    try {
      const { blob, filename } = await downloadReportExcel()
      downloadBlob(blob, filename || `hh-leads-${stamp}.xlsx`)
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
    clearProgress()
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
