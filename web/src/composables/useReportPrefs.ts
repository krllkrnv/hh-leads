import {
  DEFAULT_SYNC_DAYS,
  DONE_STORAGE_KEY,
  PREFS_STORAGE_KEY,
  EFilterKey,
  clampSyncDays,
  type FilterKey,
} from '@/types/report'
import type { Report } from '@/types/report'

export type ReportPrefs = {
  filter: FilterKey
  hideClosed: boolean
  includeKeywords: string
  excludeKeywords: string
  days: number
}

export function loadDoneMap(): Record<string, boolean> {
  try {
    return JSON.parse(localStorage.getItem(DONE_STORAGE_KEY) || '{}') as Record<string, boolean>
  } catch {
    return {}
  }
}

export function saveDoneMap(map: Record<string, boolean>): void {
  localStorage.setItem(DONE_STORAGE_KEY, JSON.stringify(map))
}

export function loadPrefs(): ReportPrefs {
  const keys = new Set<string>(Object.values(EFilterKey))
  try {
    const raw = JSON.parse(localStorage.getItem(PREFS_STORAGE_KEY) || '{}') as Partial<ReportPrefs>
    const filter = keys.has(String(raw.filter)) ? (raw.filter as FilterKey) : EFilterKey.All
    return {
      filter,
      hideClosed: raw.hideClosed ?? true,
      includeKeywords: raw.includeKeywords ?? '',
      excludeKeywords: raw.excludeKeywords ?? '',
      days: raw.days === undefined ? DEFAULT_SYNC_DAYS : clampSyncDays(raw.days),
    }
  } catch {
    return {
      filter: EFilterKey.All,
      hideClosed: true,
      includeKeywords: '',
      excludeKeywords: '',
      days: DEFAULT_SYNC_DAYS,
    }
  }
}

export function savePrefs(prefs: ReportPrefs): void {
  localStorage.setItem(PREFS_STORAGE_KEY, JSON.stringify(prefs))
}

/**
 * Убирает из локальных отметок «разобрано» id, которых больше нет в новом отчёте.
 */
export function pruneDoneMap(
  doneMap: Record<string, boolean>,
  report: Report,
): Record<string, boolean> {
  const ids = new Set(report.leads.all.map((lead) => lead.id))
  const next: Record<string, boolean> = {}
  for (const [id, value] of Object.entries(doneMap)) {
    if (ids.has(id) && value) {
      next[id] = true
    }
  }
  return next
}
