import { computed, reactive } from 'vue'
import {
  clearServerSession,
  fetchReport,
  syncReport,
  uploadReport,
} from '@/api/reportRepo'
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

type ReportState = {
  report: Report | null
  loading: boolean
  error: string
  filter: FilterKey
  query: string
  hideClosed: boolean
  doneMap: Record<string, boolean>
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
    doneMap: loadDoneMap(),
  })

  const meta = computed(() => state.report?.meta ?? null)

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
      if (!q) {
        return true
      }
      const hay = `${lead.company} ${lead.vacancy} ${lead.why} ${lead.status}`.toLowerCase()
      return hay.includes(q)
    })
  })

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
    try {
      state.report = await fetchReport()
    } catch (err) {
      state.error = err instanceof Error ? err.message : String(err)
    } finally {
      state.loading = false
    }
  }

  async function runSync(cookie: string, days: number, hhHost?: string): Promise<void> {
    state.loading = true
    state.error = ''
    try {
      state.report = await syncReport({
        cookie,
        days,
        hhHost: hhHost || undefined,
      })
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
    try {
      state.report = await uploadReport(file)
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
  }

  return {
    state,
    meta,
    filterCounts,
    visibleLeads,
    setDone,
    isDone,
    bootstrap,
    runSync,
    runUpload,
    reset,
  }
}
