import {
  EFilterKey,
  type FilterKey,
  type Lead,
  type Report,
} from '@/types/report'

export type FilterCounts = Record<FilterKey, number>

export const EMPTY_FILTER_COUNTS: FilterCounts = {
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

/**
 * Списки лидов по ключу фильтра (Call → contact в модели отчёта).
 */
export function leadsByFilter(report: Report | null | undefined): Record<FilterKey, Lead[]> | null {
  const leads = report?.leads
  if (!leads) {
    return null
  }
  return {
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
}

export function countByFilter(report: Report | null | undefined): FilterCounts {
  const byFilter = leadsByFilter(report)
  if (!byFilter) {
    return { ...EMPTY_FILTER_COUNTS }
  }
  const counts = { ...EMPTY_FILTER_COUNTS }
  for (const key of Object.values(EFilterKey)) {
    counts[key] = byFilter[key].length
  }
  return counts
}

export function getLeadsForFilter(
  report: Report | null | undefined,
  filter: FilterKey,
): Lead[] {
  const byFilter = leadsByFilter(report)
  if (!byFilter) {
    return []
  }
  return byFilter[filter] ?? byFilter[EFilterKey.All]
}
