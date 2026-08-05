<script setup lang="ts">
/**
 * Сводка по метрикам отчёта: сколько чатов, ответов, приглашений и откуда данные.
 */
import { computed } from 'vue'
import type { ReportMeta } from '@/types/report'

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
 * Форматирует ISO-дату.
 */
function formatDay(isoDate: string): string {
  const match = isoDate.match(/^(\d{4})-(\d{2})-(\d{2})/)
  if (!match) {
    return isoDate
  }
  return `${Number(match[3])} ${MONTHS_SHORT[Number(match[2]) - 1]}`
}

/**
 * Форматирует exportedAt.
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
    return 'Открыт из файла'
  }
  return props.meta.source
})

const stats = computed(() => [
  { label: 'Чатов', value: String(props.meta.total) },
  { label: 'Нужен ответ', value: String(props.meta.actions.reply), tone: 'danger' },
  { label: 'Приглашения', value: String(props.meta.invites), tone: 'warning' },
  { label: 'Собеседование', value: String(props.meta.hhStatus.interview), tone: 'success' },
])

const metaRows = computed(() => [
  { label: 'Период', value: periodLabel.value },
  { label: 'Источник', value: sourceLabel.value },
  { label: 'Обновлён', value: formatExportedAt(props.meta.exportedAt) },
  { label: 'Тестовые', value: String(props.meta.tests) },
  { label: 'Ожидание', value: String(props.meta.actions.wait) },
  { label: 'Автоответ', value: String(props.meta.actions.bot) },
])
</script>

<template>
  <section :class="$style.SummaryCharts" aria-label="Сводка">
    <div :class="$style.statsPanel">
      <div
        v-for="item in stats"
        :key="item.label"
        :class="[$style.stat, item.tone && $style[`_${item.tone}`]]"
      >
        <span :class="$style.statValue">{{ item.value }}</span>
        <span :class="$style.statLabel">{{ item.label }}</span>
      </div>
    </div>

    <ul :class="$style.meta">
      <li v-for="row in metaRows" :key="row.label" :class="$style.metaRow">
        <span :class="$style.metaLabel">{{ row.label }}</span>
        <span :class="$style.metaValue">{{ row.value }}</span>
      </li>
    </ul>
  </section>
</template>

<style module lang="scss">
.SummaryCharts {
  @include fade-up(40ms);
  display: grid;
  gap: var(--space-4);
}

.statsPanel {
  display: grid;
  gap: 0;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  background: var(--color-panel);
  border-radius: var(--radius-lg);
  overflow: hidden;

  @include respond-to(from-desktop) {
    grid-template-columns: repeat(4, minmax(0, 1fr));
  }
}

.stat {
  display: grid;
  gap: 0.45rem;
  min-width: 0;
  padding: 1.25rem 1.35rem;
  border-right: 0.0625rem solid var(--color-line);
  border-bottom: 0.0625rem solid var(--color-line);

  @include respond-to(from-desktop) {
    border-bottom: 0;

    &:last-child {
      border-right: 0;
    }
  }

  @include respond-to(tablet) {
    &:nth-child(2n) {
      border-right: 0;
    }

    &:nth-last-child(-n + 2) {
      border-bottom: 0;
    }
  }
}

.statValue {
  @include text(mono-lg);
  color: var(--color-ink);
}

.statLabel {
  @include text(caption);
  color: var(--color-faint);
}

._danger .statValue {
  color: var(--color-danger);
}

._warning .statValue {
  color: var(--color-warning);
}

._success .statValue {
  color: var(--color-success);
}

.meta {
  list-style: none;
  margin: 0;
  padding: 0;
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  background: var(--color-panel);
  border-radius: var(--radius-lg);
  overflow: hidden;

  @include respond-to(from-desktop) {
    grid-template-columns: repeat(3, minmax(0, 1fr));
  }
}

.metaRow {
  display: grid;
  gap: 0.35rem;
  min-width: 0;
  padding: 0.95rem 1.15rem;
  border-right: 0.0625rem solid var(--color-line);
  border-bottom: 0.0625rem solid var(--color-line);

  @include respond-to(from-desktop) {
    &:nth-child(3n) {
      border-right: 0;
    }

    &:nth-last-child(-n + 3) {
      border-bottom: 0;
    }
  }

  @include respond-to(tablet) {
    &:nth-child(2n) {
      border-right: 0;
    }

    &:nth-last-child(-n + 2) {
      border-bottom: 0;
    }
  }
}

.metaLabel {
  @include text(caption);
  color: var(--color-faint);
}

.metaValue {
  @include text(meta);
  color: var(--color-ink);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
</style>
