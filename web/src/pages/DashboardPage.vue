<script setup lang="ts">
/**
 * Главная страница: сначала экран загрузки, потом дашборд со списком лидов.
 */
import { nextTick, onMounted, watch } from 'vue'
import type { FilterKey } from '@/types/report'
import TheAppBar from '@/components/layout/TheAppBar.vue'
import TheFooter from '@/components/layout/TheFooter.vue'
import SetupPanel from '@/components/leads/SetupPanel.vue'
import LeadFilters from '@/components/leads/LeadFilters.vue'
import LeadsTable from '@/components/leads/LeadsTable.vue'
import SummaryCharts from '@/components/leads/SummaryCharts.vue'
import LiveProgressPanel from '@/components/leads/LiveProgressPanel.vue'
import { afterPaint, scrollToBottom, scrollToTop } from '@/lib/scrollPage'
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
 * Старт анализа — вниз до футера; успешное окончание — обратно наверх к отчёту.
 */
watch(
  () => state.loading,
  async (loading, wasLoading) => {
    if (loading) {
      await nextTick()
      await afterPaint()
      scrollToBottom()
      // Панель прогресса ещё чуть подрастает после transition — догоняем низ.
      window.setTimeout(() => scrollToBottom(), 320)
      return
    }
    if (wasLoading && state.report && !state.error && !state.showSetup) {
      await nextTick()
      await afterPaint()
      scrollToTop()
    }
  },
)

/**
 * Запускает синхронизацию чатов по cookie из формы входа.
 */
async function onSync(payload: { cookie: string; days: number; hhHost: string }): Promise<void> {
  await runSync(payload.cookie, payload.days, payload.hhHost)
}

/**
 * Разбор загруженного Excel или JSON: данные становятся текущим отчётом.
 */
async function onUpload(file: File): Promise<void> {
  await runUpload(file)
}

/**
 * Переключает активный фильтр лидов на вкладке.
 */
function onFilter(value: FilterKey): void {
  state.filter = value
}

/**
 * Сбрасывает серверную сессию и возвращает на экран загрузки.
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
        subtitle="Ниже — лиды из последней загрузки"
        show-actions
        :loading="state.loading"
        @refresh="openSetup"
        @export="exportReport"
        @reset="onReset"
      />

      <p v-if="meta?.incomplete" :class="$style.warn" role="status">
        Синхронизацию остановили раньше времени, поэтому в отчёте только часть чатов. Нажмите
        «Загрузить заново», чтобы дотянуть остальные.
      </p>

      <div :class="$style.workspace">
        <SummaryCharts v-if="meta" :meta="meta" />

        <LeadFilters
          :filter="state.filter"
          :query="state.query"
          :hide-closed="state.hideClosed"
          :include-keywords="state.includeKeywords"
          :exclude-keywords="state.excludeKeywords"
          :counts="filterCounts"
          :visible-count="visibleLeads.length"
          @update:filter="onFilter"
          @update:query="state.query = $event"
          @update:hide-closed="state.hideClosed = $event"
          @update:include-keywords="state.includeKeywords = $event"
          @update:exclude-keywords="state.excludeKeywords = $event"
        />

        <LeadsTable :leads="visibleLeads" :is-done="isDone" @toggle-done="setDone" />
      </div>
    </template>

    <LiveProgressPanel
      :active="state.loading && (state.progressMode === 'sync' || state.progressMode === 'upload')"
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
  position: relative;
  width: min(var(--content-w), calc(100% - 2rem));
  margin: 0 auto;
  padding: 0 0 var(--space-5);
  display: flex;
  flex-direction: column;
  gap: 0;
  min-height: 100dvh;
}

.workspace {
  display: grid;
  gap: var(--space-5);
  padding: var(--space-5) 0 var(--space-4);
}

.error {
  margin: var(--space-3) 0 0;
  padding: 0.85rem 1.1rem;
  border-radius: var(--radius);
  background: var(--color-danger-soft);
  color: var(--color-danger);
  @include text(caption);
}

.warn {
  margin: var(--space-3) 0 0;
  padding: 0.85rem 1.1rem;
  border-radius: var(--radius);
  background: var(--color-accent-soft);
  color: var(--color-ink);
  @include text(caption);
}
</style>
