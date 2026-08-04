<script setup lang="ts">
/**
 * Таблица лидов с priority-rail и чекбоксом «сделано».
 */
import { useCssModule } from 'vue'
import type { Lead } from '@/types/report'
import UiPill from '@/components/ui/UiPill.vue'

defineProps<{
  leads: Lead[]
  isDone: (id: string) => boolean
}>()

const emit = defineEmits<{
  toggleDone: [id: string, value: boolean]
}>()

const $style = useCssModule()

/**
 * Классы строки с учётом состояния «сделано».
 */
function rowClass(done: boolean): Array<string | false> {
  return [$style.row, done && $style._done]
}

/**
 * Переключает «сделано» для лида.
 */
function onToggleDone(id: string, event: Event): void {
  const target = event.target as HTMLInputElement
  emit('toggleDone', id, target.checked)
}
</script>

<template>
  <div :class="$style.LeadsTable">
    <p v-if="!leads.length" :class="$style.empty">
      В этой очереди пусто. Смените вкладку или сбросьте поиск.
    </p>

    <div v-else :class="$style.scroll">
      <table :class="$style.table">
        <thead>
          <tr>
            <th :class="[$style.headCell, $style.colType]">Тип</th>
            <th :class="$style.headCell">Компания</th>
            <th :class="$style.headCell">Вакансия</th>
            <th :class="$style.headCell">Статус</th>
            <th :class="$style.headCell">Суть</th>
            <th :class="[$style.headCell, $style.colDate]">Обновлён</th>
            <th :class="[$style.headCell, $style.colLink]">Чат</th>
            <th :class="[$style.headCell, $style.colDone]">Сделано</th>
          </tr>
        </thead>
        <tbody>
          <tr
            v-for="lead in leads"
            :key="lead.id"
            :class="rowClass(isDone(lead.id))"
            :data-tag="lead.tag"
          >
            <td :class="[$style.cell, $style.colType]">
              <UiPill :tag="lead.tag" />
            </td>
            <td :class="$style.cell">
              <span :class="$style.company">{{ lead.company }}</span>
            </td>
            <td :class="$style.cell">
              <a
                v-if="lead.vacancyUrl"
                :href="lead.vacancyUrl"
                target="_blank"
                rel="noreferrer"
                :class="$style.link"
              >
                {{ lead.vacancy }}
              </a>
              <span v-else :class="$style.plain">{{ lead.vacancy }}</span>
            </td>
            <td :class="$style.cell">
              <span :class="$style.status">{{ lead.status || '—' }}</span>
            </td>
            <td :class="$style.cell">
              <span :class="$style.why">{{ lead.why }}</span>
            </td>
            <td :class="[$style.cell, $style.colDate]">
              <time :class="$style.date">{{ lead.updated || '—' }}</time>
            </td>
            <td :class="[$style.cell, $style.colLink]">
              <a
                v-if="lead.chatUrl"
                :href="lead.chatUrl"
                target="_blank"
                rel="noreferrer"
                :class="$style.chatLink"
              >
                открыть
              </a>
              <span v-else :class="$style.plain">—</span>
            </td>
            <td :class="[$style.cell, $style.colDone]">
              <input
                :class="$style.checkbox"
                type="checkbox"
                :aria-label="`Отметить ${lead.company}`"
                :checked="isDone(lead.id)"
                @change="onToggleDone(lead.id, $event)"
              />
            </td>
          </tr>
        </tbody>
      </table>
    </div>
  </div>
</template>

<style module lang="scss">
.LeadsTable {
  @include fade-up(80ms);
  min-height: 12rem;
}

.scroll {
  overflow: auto;
  border: 0.0625rem solid var(--color-line);
  border-radius: var(--radius-lg);
  background: var(--color-panel);
}

.table {
  width: 100%;
  border-collapse: collapse;
  min-width: 58rem;
}

.headCell {
  position: sticky;
  top: 0;
  z-index: 1;
  padding: 0.7rem 0.8rem;
  text-align: left;
  @include text(label);
  color: var(--color-faint);
  background: var(--color-raised);
  border-bottom: 0.0625rem solid var(--color-line);
}

.cell {
  padding: 0.9rem 0.8rem;
  text-align: left;
  vertical-align: top;
  @include text(body);
  font-size: 0.9rem;
  border-bottom: 0.0625rem solid var(--color-line);
}

.row {
  position: relative;
  transition: background-color var(--dur) var(--ease);

  &::before {
    content: '';
    position: absolute;
    inset: 0 auto 0 0;
    width: 0.1875rem;
    background: var(--rail-invite);
  }

  &:hover {
    background: var(--color-raised);
  }

  &._done {
    opacity: 0.45;

    .company {
      text-decoration: line-through;
      text-decoration-thickness: 0.0625rem;
    }
  }

  &[data-tag='reply']::before {
    background: var(--rail-reply);
  }

  &[data-tag='call']::before {
    background: var(--rail-call);
  }

  &[data-tag='interview']::before {
    background: var(--rail-interview);
  }

  &[data-tag='test']::before {
    background: var(--rail-test);
  }

  &[data-tag='invite']::before {
    background: var(--rail-invite);
  }

  &[data-tag='closed']::before {
    background: var(--rail-closed);
  }
}

.company {
  font-weight: 600;
  color: var(--color-ink);
}

.link {
  font-weight: 500;
  color: var(--color-ink);
  text-decoration: none;
  border-bottom: 0.0625rem solid var(--color-line-strong);

  &:hover {
    color: var(--color-accent);
    border-color: var(--color-accent);
  }
}

.plain {
  color: var(--color-muted);
}

.why {
  display: block;
  max-width: 18rem;
  color: var(--color-muted);
  line-height: 1.4;
}

.status,
.date {
  @include text(mono);
  color: var(--color-faint);
  white-space: nowrap;
}

.chatLink {
  @include text(mono);
  color: var(--color-accent);
  text-decoration: none;
  border-bottom: 0.0625rem solid currentColor;

  &:hover {
    color: var(--color-accent-hover);
  }
}

.colType {
  width: 7.5rem;
}

.colDate {
  width: 7rem;
}

.colLink {
  width: 5rem;
}

.colDone {
  width: 4.75rem;
  text-align: center;
}

.checkbox {
  width: 1.05rem;
  height: 1.05rem;
  accent-color: var(--color-accent);
  cursor: pointer;
}

.empty {
  margin: 0;
  padding: var(--space-7) var(--space-4);
  text-align: center;
  @include text(body);
  color: var(--color-muted);
  border: 0.0625rem dashed var(--color-line);
  border-radius: var(--radius-lg);
  background: var(--color-panel);
}
</style>
