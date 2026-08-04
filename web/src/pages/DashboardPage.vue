<script setup lang="ts">
import { onMounted } from 'vue'
import SetupPanel from '@/components/leads/SetupPanel.vue'
import LeadFilters from '@/components/leads/LeadFilters.vue'
import LeadsTable from '@/components/leads/LeadsTable.vue'
import SummaryCharts from '@/components/leads/SummaryCharts.vue'
import UiButton from '@/components/ui/UiButton.vue'
import { useReport } from '@/composables/useReport'
import type { FilterKey } from '@/types/report'

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

async function onSync(payload: { cookie: string; days: number; hhHost: string }) {
  await runSync(payload.cookie, payload.days, payload.hhHost)
}

async function onUpload(file: File) {
  await runUpload(file)
}

function onFilter(value: FilterKey) {
  state.filter = value
}
</script>

<template>
  <div :class="$style.dashboardPage">
    <SetupPanel
      v-if="!state.report"
      :loading="state.loading"
      @sync="onSync"
      @upload="onUpload"
    />

    <template v-else>
      <header :class="$style.top">
        <div>
          <h1 :class="$style.title">Лиды hh</h1>
          <p :class="$style.sub">Полный список из вашего отчёта, без чужих данных.</p>
        </div>
        <div :class="$style.actions">
          <UiButton variant="ghost" :disabled="state.loading" @click="reset()">
            Сменить данные
          </UiButton>
        </div>
      </header>

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

    <p v-if="state.loading" :class="$style.status">Загрузка…</p>
    <p v-if="state.error" :class="$style.error">{{ state.error }}</p>
  </div>
</template>

<style module lang="scss">
.dashboardPage {
  width: min(72rem, calc(100% - 2rem));
  margin: 0 auto;
  padding: 1.5rem 0 3rem;
  display: grid;
  gap: 1.25rem;
}

.top {
  display: flex;
  flex-wrap: wrap;
  justify-content: space-between;
  gap: 1rem;
  align-items: end;
}

.title {
  margin: 0;
  font-family: var(--font-display);
  font-size: 2rem;
}

.sub {
  margin: 0.35rem 0 0;
  color: var(--color-muted);
}

.actions {
  display: flex;
  gap: 0.5rem;
}

.status,
.error {
  margin: 0;
}

.error {
  color: var(--color-danger);
}
</style>
