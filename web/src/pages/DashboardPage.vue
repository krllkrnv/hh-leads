<script setup lang="ts">
/**
 * Главная страница: setup или дашборд лидов.
 */
import { onMounted } from 'vue'
import type { FilterKey } from '@/types/report'
import TheAppBar from '@/components/layout/TheAppBar.vue'
import TheFooter from '@/components/layout/TheFooter.vue'
import SetupPanel from '@/components/leads/SetupPanel.vue'
import LeadFilters from '@/components/leads/LeadFilters.vue'
import LeadsTable from '@/components/leads/LeadsTable.vue'
import SummaryCharts from '@/components/leads/SummaryCharts.vue'
import { useReport } from '@/composables/useReport'

const {
  state,
  meta,
  filterCounts,
  visibleLeads,
  setDone,
  isDone,
  bootstrap,
  runSync,
  runUpload,
  reset,
} = useReport()

onMounted(() => {
  void bootstrap()
})

/**
 * Синхронизация по cookie из SetupPanel.
 */
async function onSync(payload: {
  cookie: string
  days: number
  hhHost: string
}): Promise<void> {
  await runSync(payload.cookie, payload.days, payload.hhHost)
}

/**
 * Загрузка файла отчёта.
 */
async function onUpload(file: File): Promise<void> {
  await runUpload(file)
}

/**
 * Смена активной очереди.
 */
function onFilter(value: FilterKey): void {
  state.filter = value
}

/**
 * Сброс сессии и возврат на setup.
 */
async function onReset(): Promise<void> {
  await reset()
}
</script>

<template>
  <div :class="$style.DashboardPage">
    <SetupPanel
      v-if="!state.report"
      :loading="state.loading"
      @sync="onSync"
      @upload="onUpload"
    />

    <template v-else>
      <TheAppBar
        subtitle="Фильтры и список из вашего отчёта"
        show-reset
        :loading="state.loading"
        @reset="onReset"
      />

      <SummaryCharts v-if="meta" :meta="meta" />

      <LeadFilters
        :filter="state.filter"
        :query="state.query"
        :hide-closed="state.hideClosed"
        :counts="filterCounts"
        :visible-count="visibleLeads.length"
        @update:filter="onFilter"
        @update:query="state.query = $event"
        @update:hide-closed="state.hideClosed = $event"
      />

      <LeadsTable
        :leads="visibleLeads"
        :is-done="isDone"
        @toggle-done="setDone"
      />
    </template>

    <div
      v-if="state.loading"
      :class="$style.status"
      role="status"
      aria-live="polite"
    >
      Загрузка данных…
    </div>
    <p v-if="state.error" :class="$style.error" role="alert">
      {{ state.error }}
    </p>

    <TheFooter />
  </div>
</template>

<style module lang="scss">
.DashboardPage {
  width: min(var(--content-w), calc(100% - 2rem));
  margin: 0 auto;
  padding: 0 0 var(--space-4);
  display: flex;
  flex-direction: column;
  gap: var(--space-2);
  min-height: 100dvh;
}

.status {
  margin: var(--space-3) 0 0;
  @include text(mono);
  color: var(--color-muted);
}

.error {
  margin: var(--space-3) 0 0;
  padding: 0.85rem 1rem;
  border-left: 0.125rem solid var(--color-danger);
  background: var(--color-danger-soft);
  color: var(--color-danger);
  @include text(caption);
}
</style>
