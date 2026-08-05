export type LeadTag =
  'reply' | 'call' | 'interview' | 'test' | 'invite' | 'wait' | 'bot' | 'discuss' | 'closed'

export type Lead = {
  id: string
  company: string
  vacancy: string
  status: string
  stateId?: string
  tag: LeadTag
  action: string
  why: string
  summary?: string
  updated: string
  chatUrl: string
  vacancyUrl: string
  closed: boolean
  strong: boolean
  categories?: string[]
  inviteReasons?: string[]
  testReasons?: string[]
  lastFrom?: string
}

export type ReportMeta = {
  period: string
  periodFrom?: string | null
  days: number
  exportedAt: string
  source: string
  total: number
  invites: number
  tests: number
  discussions: number
  multiCategory: number
  actions: {
    reply: number
    interview: number
    test: number
    wait: number
    bot: number
    closed: number
  }
  hhStatus: {
    response: number
    reject: number
    interview: number
  }
  actionCounts?: Record<string, number>
  stateCounts?: Record<string, number>
}

export type Report = {
  meta: ReportMeta
  leads: {
    all: Lead[]
    reply: Lead[]
    interview: Lead[]
    contact: Lead[]
    tests: Lead[]
    invites: Lead[]
    wait?: Lead[]
    bot?: Lead[]
    closed: Lead[]
  }
  records?: Lead[]
}

export enum EFilterKey {
  All = 'all',
  Reply = 'reply',
  Call = 'call',
  Interview = 'interview',
  Test = 'test',
  Invites = 'invites',
  Wait = 'wait',
  Bot = 'bot',
  Closed = 'closed',
}

export type FilterKey = `${EFilterKey}`

export enum EButtonVariant {
  Primary = 'primary',
  Ghost = 'ghost',
  Danger = 'danger',
}

export enum EButtonSize {
  Small = 'small',
  Medium = 'medium',
}

export enum EStatTone {
  Default = 'default',
  Warning = 'warning',
  Danger = 'danger',
  Success = 'success',
}

export const FILTER_LABELS: Record<FilterKey, string> = {
  [EFilterKey.All]: 'Все',
  [EFilterKey.Reply]: 'Нужен ответ',
  [EFilterKey.Call]: 'Связаться',
  [EFilterKey.Interview]: 'Собеседование',
  [EFilterKey.Test]: 'Тестовое',
  [EFilterKey.Invites]: 'Приглашения',
  [EFilterKey.Wait]: 'Ожидание',
  [EFilterKey.Bot]: 'Автоответ',
  [EFilterKey.Closed]: 'Закрытые',
}

export const LEAD_TAG_LABELS: Record<LeadTag, string> = {
  reply: 'нужен ответ',
  call: 'связаться',
  interview: 'собеседование',
  test: 'тестовое',
  invite: 'приглашение',
  wait: 'ожидание',
  bot: 'автоответ',
  discuss: 'обсуждение',
  closed: 'закрыто',
}

export const DEFAULT_SYNC_DAYS = 60
export const DONE_STORAGE_KEY = 'hh-leads-done'
export const PREFS_STORAGE_KEY = 'hh-leads-prefs'
export const SESSION_STORAGE_KEY = 'hh-leads-session-id'
