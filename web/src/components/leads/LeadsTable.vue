<script setup lang="ts">
/**
 * Очередь лидов: компания + вакансия, суть, чат как главное действие.
 */
import { useCssModule } from 'vue'
import type { Lead } from '@/types/report'
import UiPill from '@/components/ui/UiPill.vue'
import { displayUpdated, displayWhy } from '@/lib/leadDisplay'

defineProps<{
  leads: Lead[]
  isDone: (id: string) => boolean
}>()

const emit = defineEmits<{
  toggleDone: [id: string, value: boolean]
}>()

const $style = useCssModule()

/**
 * Классы строки с учётом «сделано».
 */
function rowClass(done: boolean): Array<string | false> {
  return [$style.row, done && $style._done]
}

/**
 * Переключает «сделано».
 */
function onToggleDone(id: string, event: Event): void {
  const target = event.target as HTMLInputElement
  emit('toggleDone', id, target.checked)
}

/**
 * Открывает чат в новой вкладке.
 */
function openChat(lead: Lead): void {
  if (!lead.chatUrl) {
    return
  }
  window.open(lead.chatUrl, '_blank', 'noopener,noreferrer')
}

/**
 * Клик по строке → чат (кроме ссылок и чекбокса).
 */
function onRowActivate(lead: Lead, event: MouseEvent): void {
  const target = event.target as HTMLElement
  if (target.closest('a, button, input, label')) {
    return
  }
  openChat(lead)
}

/**
 * Показывает статус только если он не пустой и не банальный «Отклик».
 */
function showStatus(status: string): boolean {
  const value = status.trim()
  if (!value || value === '—') {
    return false
  }
  return !/^отклик$/i.test(value)
}
</script>

<template>
  <div :class="$style.LeadsTable">
    <p v-if="!leads.length" :class="$style.empty">
      В этой очереди пусто. Смените вкладку или сбросьте поиск.
    </p>

    <ul v-else :class="$style.list">
      <li
        v-for="lead in leads"
        :key="lead.id"
        :class="rowClass(isDone(lead.id))"
        :data-tag="lead.tag"
        :tabindex="lead.chatUrl ? 0 : undefined"
        :role="lead.chatUrl ? 'link' : undefined"
        @click="onRowActivate(lead, $event)"
        @keydown.enter="openChat(lead)"
        @keydown.space.prevent="openChat(lead)"
      >
        <div :class="$style.rail" aria-hidden="true" />

        <div :class="$style.main">
          <div :class="$style.top">
            <UiPill :tag="lead.tag" />
            <span :class="$style.company">{{ lead.company }}</span>
            <time :class="$style.date" :datetime="lead.updated">
              {{ displayUpdated(lead.updated) }}
            </time>
          </div>

          <div :class="$style.vacancyLine">
            <a
              v-if="lead.vacancyUrl"
              :href="lead.vacancyUrl"
              target="_blank"
              rel="noreferrer"
              :class="$style.vacancy"
              :title="lead.vacancy"
            >
              {{ lead.vacancy }}
            </a>
            <span v-else :class="$style.vacancyPlain" :title="lead.vacancy">
              {{ lead.vacancy }}
            </span>
            <span v-if="showStatus(lead.status)" :class="$style.status">
              {{ lead.status }}
            </span>
          </div>

          <p :class="$style.why" :title="displayWhy(lead.why)">
            {{ displayWhy(lead.why) }}
          </p>
        </div>

        <div :class="$style.actions" @click.stop>
          <a
            v-if="lead.chatUrl"
            :href="lead.chatUrl"
            target="_blank"
            rel="noreferrer"
            :class="$style.chatBtn"
          >
            Чат
          </a>
          <span v-else :class="$style.noChat">нет чата</span>

          <label :class="$style.done">
            <input
              :class="$style.checkbox"
              type="checkbox"
              :aria-label="`Отметить ${lead.company}`"
              :checked="isDone(lead.id)"
              @change="onToggleDone(lead.id, $event)"
            />
            <span :class="$style.doneLabel">готово</span>
          </label>
        </div>
      </li>
    </ul>
  </div>
</template>

<style module lang="scss">
.LeadsTable {
  @include fade-up(80ms);
  min-height: 12rem;
}

.list {
  list-style: none;
  margin: 0;
  padding: 0;
  border: 0.0625rem solid var(--color-line);
  border-radius: var(--radius-lg);
  background: var(--color-panel);
  overflow: hidden;
}

.row {
  position: relative;
  display: grid;
  grid-template-columns: 0.1875rem minmax(0, 1fr) auto;
  gap: 0;
  padding: 0;
  border-bottom: 0.0625rem solid var(--color-line);
  cursor: pointer;
  transition: background-color var(--dur) var(--ease);

  &:last-child {
    border-bottom: 0;
  }

  &:hover,
  &:focus-visible {
    background: var(--color-raised);
    outline: none;
  }

  &._done {
    opacity: 0.48;

    .company {
      text-decoration: line-through;
      text-decoration-thickness: 0.0625rem;
    }
  }
}

.rail {
  background: var(--rail-invite);

  .row[data-tag='reply'] & {
    background: var(--rail-reply);
  }

  .row[data-tag='call'] & {
    background: var(--rail-call);
  }

  .row[data-tag='interview'] & {
    background: var(--rail-interview);
  }

  .row[data-tag='test'] & {
    background: var(--rail-test);
  }

  .row[data-tag='invite'] & {
    background: var(--rail-invite);
  }

  .row[data-tag='wait'] & {
    background: var(--rail-wait);
  }

  .row[data-tag='bot'] & {
    background: var(--rail-bot);
  }

  .row[data-tag='discuss'] & {
    background: var(--rail-discuss);
  }

  .row[data-tag='closed'] & {
    background: var(--rail-closed);
  }
}

.main {
  min-width: 0;
  padding: 0.85rem 1rem;
  display: grid;
  gap: 0.35rem;
}

.top {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 0.55rem 0.75rem;
}

.company {
  flex: 1 1 10rem;
  min-width: 0;
  font-weight: 650;
  color: var(--color-ink);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.date {
  @include text(mono);
  color: var(--color-faint);
  white-space: nowrap;
  margin-left: auto;
}

.vacancyLine {
  display: flex;
  flex-wrap: wrap;
  align-items: baseline;
  gap: 0.45rem 0.75rem;
  min-width: 0;
}

.vacancy,
.vacancyPlain {
  min-width: 0;
  max-width: 100%;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  font-weight: 500;
  color: var(--color-ink);
}

.vacancy {
  text-decoration: none;
  border-bottom: 0.0625rem solid var(--color-line-strong);

  &:hover {
    color: var(--color-accent);
    border-color: var(--color-accent);
  }
}

.vacancyPlain {
  color: var(--color-muted);
}

.status {
  @include text(mono);
  font-size: 0.6875rem;
  color: var(--color-faint);
  white-space: nowrap;
}

.why {
  margin: 0;
  max-width: 42rem;
  color: var(--color-muted);
  line-height: 1.45;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
  @include text(body);
  font-size: 0.875rem;
}

.actions {
  display: flex;
  flex-direction: column;
  align-items: stretch;
  justify-content: center;
  gap: 0.55rem;
  padding: 0.85rem 1rem 0.85rem 0;
  min-width: 6.5rem;
}

.chatBtn {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  min-height: 2rem;
  padding: 0 0.85rem;
  border-radius: var(--radius-sm);
  background: var(--color-accent);
  color: #fff;
  text-decoration: none;
  @include text(caption);
  font-weight: 650;
  transition: background-color var(--dur) var(--ease);

  &:hover {
    background: var(--color-accent-hover);
  }
}

.noChat {
  @include text(mono);
  color: var(--color-faint);
  text-align: center;
}

.done {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 0.35rem;
  cursor: pointer;
  user-select: none;
}

.checkbox {
  width: 1rem;
  height: 1rem;
  accent-color: var(--color-accent);
  cursor: pointer;
}

.doneLabel {
  @include text(mono);
  font-size: 0.6875rem;
  color: var(--color-faint);
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

@include respond-to(tablet) {
  .row {
    grid-template-columns: 0.1875rem minmax(0, 1fr);
  }

  .actions {
    grid-column: 2;
    flex-direction: row;
    align-items: center;
    justify-content: flex-start;
    padding: 0 1rem 0.85rem;
    min-width: 0;
  }

  .date {
    margin-left: 0;
    width: 100%;
    order: 3;
  }

  .top {
    .date {
      margin-left: auto;
      width: auto;
      order: 0;
    }
  }
}
</style>
