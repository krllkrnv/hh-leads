<script setup lang="ts">
import type { ReportMeta } from '@/types/report'
import StatCard from '@/components/ui/StatCard.vue'

defineProps<{
  meta: ReportMeta
}>()
</script>

<template>
  <section :class="$style.summaryCharts">
    <div :class="$style.stats">
      <StatCard :value="String(meta.total)" label="Чатов" />
      <StatCard
        :value="String(meta.invites)"
        label="Приглашения"
        tone="warning"
      />
      <StatCard
        :value="String(meta.actions.reply)"
        label="Ответить HR"
        tone="danger"
      />
      <StatCard
        :value="String(meta.hhStatus.interview)"
        label="Статус hh: собеседование"
        tone="success"
      />
    </div>
    <div :class="$style.metaLine">
      {{ meta.period }} · источник {{ meta.source }} · выгрузка
      {{ meta.exportedAt }} · тестов {{ meta.tests }} · обсуждений
      {{ meta.discussions }} · ждать HR {{ meta.actions.wait }}
    </div>
  </section>
</template>

<style module lang="scss">
.summaryCharts {
  display: grid;
  gap: 0.75rem;
}

.stats {
  display: grid;
  gap: 0.75rem;
  grid-template-columns: repeat(2, minmax(0, 1fr));

  @media (min-width: 56rem) {
    grid-template-columns: repeat(4, minmax(0, 1fr));
  }
}

.metaLine {
  color: var(--color-muted);
  font-size: 0.875rem;
}
</style>
