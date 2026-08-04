import { computed, reactive } from 'vue'
import {
  clearServerSession,
  fetchReport,
  syncReport,
  uploadReport,
} from '@/api/reportRepo'
import type { FilterKey, Lead, Report } from '@/types/report'

const DONE_KEY = 'hh-leads-done'

function loadDoneMap(): Record<string, boolean> {
  try {
    return JSON.parse(localStorage.getItem(DONE_KEY) || '{}') as Record<string, boolean>
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

export function useReport() {
  const state = reactive<ReportState>({
    report: null,
    loading: false,
    error: '',
    filter: 'all',
    query: '',
    hideClosed: true,
    doneMap: loadDoneMap(),
  })

  const meta = computed(() => state.report?.meta ?? null)

  const filterCounts = computed(() => {
    const leads = state.report?.leads
    if (!leads) {
      return {
        all: 0,
        reply: 0,
        call: 0,
        interview: 0,
        test: 0,
        invites: 0,
        closed: 0,
      }
    }
    return {
      all: leads.all.length,
      reply: leads.reply.length,
      call: leads.contact.length,
      interview: leads.interview.length,
      test: leads.tests.length,
      invites: leads.invites.length,
      closed: leads.closed.length,
    }
  })

  const visibleLeads = computed(() => {
    const leads = state.report?.leads
    if (!leads) return [] as Lead[]

    let list: Lead[]
    switch (state.filter) {
      case 'reply':
        list = leads.reply
        break
      case 'call':
        list = leads.contact
        break
      case 'interview':
        list = leads.interview
        break
      case 'test':
        list = leads.tests
        break
      case 'invites':
        list = leads.invites
        break
      case 'closed':
        list = leads.closed
        break
      default:
        list = leads.all
    }

    const q = state.query.trim().toLowerCase()
    return list.filter((lead) => {
      if (
        state.hideClosed
        && state.filter !== 'closed'
        && (lead.closed || lead.tag === 'closed')
      ) {
        return false
      }
      if (!q) return true
      const hay = `${lead.company} ${lead.vacancy} ${lead.why} ${lead.status}`.toLowerCase()
      return hay.includes(q)
    })
  })

  function setDone(id: string, value: boolean) {
    state.doneMap = { ...state.doneMap, [id]: value }
    localStorage.setItem(DONE_KEY, JSON.stringify(state.doneMap))
  }

  function isDone(id: string) {
    return Boolean(state.doneMap[id])
  }

  async function bootstrap() {
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

  async function runSync(cookie: string, days: number, hhHost?: string) {
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

  async function runUpload(file: File) {
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

  async function reset() {
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
