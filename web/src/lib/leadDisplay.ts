import type { Lead } from '@/types/report'

const WHY_PREFIX =
  /^(?:последнее от HR|бот|последнее от тебя|автоответ)\s*[:·]\s*/i

const FRONTEND_RE =
  /frontend|front[\s-]?end|фронт[\s-]?енд|фронтенд|vue|nuxt|react|angular|typescript|\bts\b|javascript|\bjs\b|svelte|next\.?js|css|html|web[\s-]?разработ/i

const NON_FRONTEND_STACK_RE =
  /\bc#\b|asp\.?\s?net|\.net\b|ms\s?sql|1[сc][\s-]?битрикс|битрикс|bitrix|php\b|laravel|java\b|kotlin|swift|golang|\bgo\b|python|django|flask|1с\b|1c\b/i

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
 * Вакансия выглядит как frontend / web UI.
 */
export function isFrontendLead(lead: Lead): boolean {
  const hay = `${lead.vacancy} ${lead.company} ${lead.why}`
  if (FRONTEND_RE.test(hay)) {
    return true
  }
  // Явно другой стек без frontend-маркеров — не подходит.
  if (NON_FRONTEND_STACK_RE.test(hay)) {
    return false
  }
  return false
}
