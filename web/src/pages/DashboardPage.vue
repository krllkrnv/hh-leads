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
import LiveProgressPanel from '@/components/leads/LiveProgressPanel.vue'
import { useReport } from '@/composables/useReport'

const {
  state,
  meta,
  filterCounts,
  visibleLeads,
  progressPercent,
  setDone,
  isDone,
  bootstrap,
  runSync,
  runUpload,
  cancelJob,
  exportReport,
  openSetup,
  closeSetup,
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
      v-if="!state.report || state.showSetup"
      :loading="state.loading"
      :can-cancel-setup="Boolean(state.report)"
      @sync="onSync"
      @upload="onUpload"
      @cancel-setup="closeSetup"
    />

    <template v-if="state.report && !state.showSetup">
      <TheAppBar
        subtitle="Очередь лидов из чатов hh.ru"
        show-actions
        :loading="state.loading"
        @refresh="openSetup"
        @export="exportReport"
        @reset="onReset"
      />

      <SummaryCharts v-if="meta" :meta="meta" />

      <LeadFilters
        :filter="state.filter"
        :query="state.query"
        :hide-closed="state.hideClosed"
        :frontend-only="state.frontendOnly"
        :counts="filterCounts"
        :visible-count="visibleLeads.length"
        @update:filter="onFilter"
        @update:query="state.query = $event"
        @update:hide-closed="state.hideClosed = $event"
        @update:frontend-only="state.frontendOnly = $event"
      />

      <LeadsTable
        :leads="visibleLeads"
        :is-done="isDone"
        @toggle-done="setDone"
      />
    </template>

    <LiveProgressPanel
      :active="state.loading"
      :mode="state.progressMode"
      :stage="state.progressStage"
      :message="state.progressMessage"
      :current="state.progressCurrent"
      :total="state.progressTotal"
      :percent="progressPercent"
      :logs="state.progressLogs"
      @cancel="cancelJob"
    />

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

.error {
  margin: var(--space-3) 0 0;
  padding: 0.85rem 1rem;
  border-left: 0.125rem solid var(--color-danger);
  background: var(--color-danger-soft);
  color: var(--color-danger);
  @include text(caption);
}
</style>
