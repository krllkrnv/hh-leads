export type LeadTag =
  | 'reply'
  | 'call'
  | 'interview'
  | 'test'
  | 'invite'
  | 'closed'

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
    closed: Lead[]
  }
  records?: Lead[]
}

export type FilterKey =
  | 'all'
  | 'reply'
  | 'call'
  | 'interview'
  | 'test'
  | 'invites'
  | 'closed'
