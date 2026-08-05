import type { Lead } from '@/types/report'

const WHY_PREFIX =
  /^(?:последнее от HR|бот|последнее от тебя|автоответ)\s*[:·]\s*/i

/**
 * Читаемый фрагмент «сути» без служебных префиксов.
 */
export function displayWhy(why: string): string {
  const cleaned = why.replace(/\s+/g, ' ').trim().replace(WHY_PREFIX, '')
  return cleaned || '—'
}

/**
 * Короткая дата для списка: сегодня/вчера или дд.мм HH:mm.
 */
export function displayUpdated(raw: string): string {
  const value = raw.trim()
  if (!value || value === '—') {
    return '—'
  }

  const match = value.match(
    /^(\d{4})-(\d{2})-(\d{2})(?:[ T](\d{2}):(\d{2}))?/,
  )
  if (!match) {
    return value
  }

  const [, y, m, d, hh = '00', mm = '00'] = match
  const date = new Date(Number(y), Number(m) - 1, Number(d), Number(hh), Number(mm))
  if (Number.isNaN(date.getTime())) {
    return value
  }

  const now = new Date()
  const startToday = new Date(now.getFullYear(), now.getMonth(), now.getDate())
  const startThat = new Date(date.getFullYear(), date.getMonth(), date.getDate())
  const dayDiff = Math.round((startToday.getTime() - startThat.getTime()) / 86_400_000)
  const time = `${hh}:${mm}`

  if (dayDiff === 0) {
    return `сегодня ${time}`
  }
  if (dayDiff === 1) {
    return `вчера ${time}`
  }
  return `${d}.${m} ${time}`
}

/**
 * Разбивает строку ключевых слов: запятая / точка с запятой / перевод строки.
 */
export function parseKeywords(raw: string): string[] {
  return raw
    .split(/[,;\n]+/)
    .map((part) => part.trim().toLowerCase())
    .filter(Boolean)
}

function leadHaystack(lead: Lead): string {
  return `${lead.company} ${lead.vacancy} ${lead.why} ${lead.status}`.toLowerCase()
}

/**
 * Лид проходит фильтр профиля: все include есть, ни одного exclude нет.
 */
export function matchesProfile(
  lead: Lead,
  includeRaw: string,
  excludeRaw: string,
): boolean {
  const hay = leadHaystack(lead)
  const include = parseKeywords(includeRaw)
  const exclude = parseKeywords(excludeRaw)

  if (include.length && !include.every((term) => hay.includes(term))) {
    return false
  }
  if (exclude.length && exclude.some((term) => hay.includes(term))) {
    return false
  }
  return true
}
