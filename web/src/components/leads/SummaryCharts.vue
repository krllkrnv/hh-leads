<script setup lang="ts">
/**
 * Сводка метрик отчёта.
 */
import type { ReportMeta } from '@/types/report'
import { EStatTone } from '@/types/report'
import StatCard from '@/components/ui/StatCard.vue'

defineProps<{
  meta: ReportMeta
}>()
</script>

<template>
  <section :class="$style.SummaryCharts" aria-label="Сводка">
    <div :class="$style.stats">
      <StatCard :value="String(meta.total)" label="Чатов" />
      <StatCard
        :value="String(meta.invites)"
        label="Приглашения"
        :tone="EStatTone.Warning"
      />
      <StatCard
        :value="String(meta.actions.reply)"
        label="Ответить"
        :tone="EStatTone.Danger"
      />
      <StatCard
        :value="String(meta.hhStatus.interview)"
        label="Собес"
        :tone="EStatTone.Success"
      />
    </div>
    <p :class="$style.metaLine">
      <span>{{ meta.period }}</span>
      <span :class="$style.sep">/</span>
      <span>{{ meta.source }}</span>
      <span :class="$style.sep">/</span>
      <span>{{ meta.exportedAt }}</span>
      <span :class="$style.sep">/</span>
      <span>тесты {{ meta.tests }}</span>
      <span :class="$style.sep">/</span>
      <span>ждать {{ meta.actions.wait }}</span>
    </p>
  </section>
</template>

<style module lang="scss">
.SummaryCharts {
  @include fade-up(40ms);
  display: grid;
  gap: var(--space-4);
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

.metaLine {
  margin: 0;
  display: flex;
  flex-wrap: wrap;
  gap: 0.2rem 0;
  @include text(mono);
  color: var(--color-faint);
}

.sep {
  margin: 0 0.45rem;
  color: var(--color-line-strong);
}
</style>
