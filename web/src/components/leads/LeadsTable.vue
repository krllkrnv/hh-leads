<script setup lang="ts">
import type { Lead } from '@/types/report'
import UiPill from '@/components/ui/UiPill.vue'

defineProps<{
  leads: Lead[]
  isDone: (id: string) => boolean
}>()

defineEmits<{
  toggleDone: [id: string, value: boolean]
}>()
</script>

<template>
  <div :class="$style.leadsTable">
    <table>
      <thead>
        <tr>
          <th>Тип</th>
          <th>Компания</th>
          <th>Вакансия</th>
          <th>Статус</th>
          <th>Суть</th>
          <th>Обновлён</th>
          <th>Чат</th>
          <th>Сделано</th>
        </tr>
      </thead>
      <tbody>
        <tr v-for="lead in leads" :key="lead.id">
          <td><UiPill :tag="lead.tag" /></td>
          <td>{{ lead.company }}</td>
          <td>
            <a
              v-if="lead.vacancyUrl"
              :href="lead.vacancyUrl"
              target="_blank"
              rel="noreferrer"
            >
              {{ lead.vacancy }}
            </a>
            <span v-else>{{ lead.vacancy }}</span>
          </td>
          <td>{{ lead.status || '—' }}</td>
          <td :class="$style.why">{{ lead.why }}</td>
          <td>{{ lead.updated || '—' }}</td>
          <td>
            <a
              v-if="lead.chatUrl"
              :href="lead.chatUrl"
              target="_blank"
              rel="noreferrer"
            >
              открыть
            </a>
            <span v-else>—</span>
          </td>
          <td>
            <input
              type="checkbox"
              :checked="isDone(lead.id)"
              @change="
                $emit(
                  'toggleDone',
                  lead.id,
                  ($event.target as HTMLInputElement).checked,
                )
              "
            />
          </td>
        </tr>
      </tbody>
    </table>
    <p v-if="!leads.length" :class="$style.empty">
      В этой вкладке нет строк при текущих фильтрах.
    </p>
  </div>
</template>

<style module lang="scss">
.leadsTable {
  overflow: auto;
  border: 0.0625rem solid var(--color-border);
  border-radius: 0.75rem;
  background: var(--color-surface);

  table {
    width: 100%;
    border-collapse: collapse;
    min-width: 56rem;
  }

  th,
  td {
    padding: 0.7rem 0.75rem;
    border-bottom: 0.0625rem solid var(--color-border);
    text-align: left;
    vertical-align: top;
    font-size: 0.9rem;
  }

  th {
    font-size: 0.75rem;
    text-transform: uppercase;
    letter-spacing: 0.04em;
    color: var(--color-muted);
    background: #fafaf9;
    position: sticky;
    top: 0;
  }

  tbody tr:last-child td {
    border-bottom: 0;
  }
}

.why {
  max-width: 18rem;
  color: var(--color-muted);
}

.empty {
  margin: 0;
  padding: 1.25rem;
  color: var(--color-muted);
}
</style>
