<script setup lang="ts">
/**
 * Сводка метрик и метаданных отчёта.
 */
import { computed } from 'vue'
import type { ReportMeta } from '@/types/report'
import { EStatTone } from '@/types/report'
import StatCard from '@/components/ui/StatCard.vue'

const props = defineProps<{
  meta: ReportMeta
}>()

const MONTHS_SHORT = [
  'янв',
  'фев',
  'мар',
  'апр',
  'мая',
  'июн',
  'июл',
  'авг',
  'сен',
  'окт',
  'ноя',
  'дек',
]

/**
 * Форматирует ISO-дату в короткий русский вид.
 */
function formatDay(isoDate: string): string {
  const match = isoDate.match(/^(\d{4})-(\d{2})-(\d{2})/)
  if (!match) {
    return isoDate
  }
  const day = Number(match[3])
  const month = Number(match[2]) - 1
  return `${day} ${MONTHS_SHORT[month]}`
}

/**
 * Форматирует exportedAt: 2026-08-04 19:16 → 4 авг, 19:16
 */
function formatExportedAt(raw: string): string {
  const match = raw.match(/^(\d{4})-(\d{2})-(\d{2})(?:[ T](\d{2}):(\d{2}))?/)
  if (!match) {
    return raw
  }
  const day = Number(match[3])
  const month = Number(match[2]) - 1
  const time = match[4] && match[5] ? `${match[4]}:${match[5]}` : ''
  return time ? `${day} ${MONTHS_SHORT[month]}, ${time}` : `${day} ${MONTHS_SHORT[month]}`
}

const periodLabel = computed(() => {
  const days = props.meta.days
  const from = props.meta.periodFrom
  if (from) {
    return `${formatDay(from)} — сейчас · ${days} дн.`
  }
  return `Последние ${days} дней`
})

const sourceLabel = computed(() => {
  if (props.meta.source === 'sync') {
    return 'Синхронизация с hh.ru'
  }
  if (props.meta.source === 'upload') {
    return 'Загрузка файла'
  }
  return props.meta.source
})

const metaRows = computed(() => [
  { label: 'Период', value: periodLabel.value },
  { label: 'Источник', value: sourceLabel.value },
  { label: 'Обновлён', value: formatExportedAt(props.meta.exportedAt) },
  { label: 'Тесты', value: String(props.meta.tests) },
  { label: 'Ждём ответа', value: String(props.meta.actions.wait) },
  { label: 'Бот', value: String(props.meta.actions.bot) },
])
</script>

<template>
  <section :class="$style.SummaryCharts" aria-label="Сводка">
    <div :class="$style.stats">
      <StatCard :value="String(meta.total)" label="Чатов" />
      <StatCard
        :value="String(meta.actions.reply)"
        label="Ответить"
        :tone="EStatTone.Danger"
      />
      <StatCard
        :value="String(meta.invites)"
        label="Приглашения"
        :tone="EStatTone.Warning"
      />
      <StatCard
        :value="String(meta.hhStatus.interview)"
        label="Собес"
        :tone="EStatTone.Success"
      />
    </div>

    <dl :class="$style.meta">
      <div v-for="row in metaRows" :key="row.label" :class="$style.metaRow">
        <dt :class="$style.metaLabel">{{ row.label }}</dt>
        <dd :class="$style.metaValue">{{ row.value }}</dd>
      </div>
    </dl>
  </section>
</template>

<style module lang="scss">
.SummaryCharts {
  @include fade-up(40ms);
  display: grid;
  gap: var(--space-5);
  padding: var(--space-5) 0;
  border-bottom: 0.0625rem solid var(--color-line);
}

.stats {
  display: grid;
  gap: var(--space-5);
  grid-template-columns: repeat(2, minmax(0, 1fr));

  @include respond-to(from-desktop) {
    grid-template-columns: repeat(4, minmax(0, 1fr));
  }
}

.meta {
  margin: 0;
  display: grid;
  gap: 0.55rem 2rem;
  grid-template-columns: repeat(2, minmax(0, 1fr));

  @include respond-to(from-desktop) {
    grid-template-columns: repeat(3, minmax(0, 1fr));
  }
}

.metaRow {
  display: flex;
  align-items: baseline;
  justify-content: space-between;
  gap: 0.75rem;
  min-width: 0;
  padding-bottom: 0.45rem;
  border-bottom: 0.0625rem solid var(--color-line);
}

.metaLabel {
  @include text(caption);
  color: var(--color-faint);
  flex-shrink: 0;
}

.metaValue {
  margin: 0;
  @include text(caption);
  font-weight: 600;
  color: var(--color-ink);
  text-align: right;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
</style>
