<script setup lang="ts">
/**
 * Список лидов. Клик по строке открывает чат на hh в новой вкладке.
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
 * Собирает CSS-классы строки: «разобрано» и кликабельность.
 */
function rowClass(done: boolean, hasChat: boolean): Array<string | false> {
  return [$style.row, done && $style._done, hasChat && $style._clickable]
}

/**
 * Ставит или снимает локальную отметку «уже разобрал этот лид».
 */
function onToggleDone(id: string, event: Event): void {
  const target = event.target as HTMLInputElement
  emit('toggleDone', id, target.checked)
}

/**
 * Открывает чат работодателя на hh.ru.
 */
function openChat(lead: Lead): void {
  if (!lead.chatUrl) {
    return
  }
  window.open(lead.chatUrl, '_blank', 'noopener,noreferrer')
}

/**
 * Клик по строке открывает чат, если не кликнули по ссылке, кнопке или чекбоксу.
 */
function onRowActivate(lead: Lead, event: MouseEvent): void {
  const target = event.target as HTMLElement
  if (target.closest('a, button, input, label')) {
    return
  }
  openChat(lead)
}

/**
 * Показывает статус hh только когда он информативнее обычного «Отклик».
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
      В этом списке пока пусто. Попробуйте другую вкладку или ослабьте фильтр по словам в профиле.
    </p>

    <ul v-else :class="$style.list">
      <li
        v-for="lead in leads"
        :key="lead.id"
        :class="rowClass(isDone(lead.id), Boolean(lead.chatUrl))"
        :tabindex="lead.chatUrl ? 0 : undefined"
        :role="lead.chatUrl ? 'button' : undefined"
        :aria-label="lead.chatUrl ? `Открыть чат: ${lead.company}` : undefined"
        @click="onRowActivate(lead, $event)"
        @keydown.enter="openChat(lead)"
        @keydown.space.prevent="openChat(lead)"
      >
        <div :class="$style.main">
          <div :class="$style.head">
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

        <label
          :class="$style.done"
          title="Личная пометка только в этом браузере: вы уже ответили или разобрали этот чат."
          @click.stop
        >
          <input
            :class="$style.checkbox"
            type="checkbox"
            :aria-label="`Отметить разобранным чат с ${lead.company}`"
            :checked="isDone(lead.id)"
            @change="onToggleDone(lead.id, $event)"
          />
          <span :class="$style.doneLabel">разобрано</span>
        </label>
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
  background: var(--color-panel);
  border-radius: var(--radius-lg);
  overflow: hidden;
}

.row {
  display: grid;
  grid-template-columns: minmax(0, 1fr) auto;
  gap: 1rem;
  align-items: start;
  padding: 1.05rem 1.2rem;
  border-bottom: 0.0625rem solid var(--color-line);

  &:last-child {
    border-bottom: 0;
  }

  &._clickable {
    cursor: pointer;

    &:focus-visible {
      outline: none;
    }
  }

  &._done {
    opacity: 0.42;

    .company {
      text-decoration: line-through;
      text-decoration-thickness: 0.0625rem;
    }
  }
}

.main {
  min-width: 0;
  display: grid;
  gap: 0.35rem;
}

.head {
  display: grid;
  grid-template-columns: auto minmax(0, 1fr) auto;
  align-items: center;
  gap: 0.65rem;
  min-width: 0;
}

.company {
  min-width: 0;
  font-size: 1rem;
  font-weight: 600;
  letter-spacing: 0.004em;
  color: var(--color-ink);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.date {
  @include text(mono);
  color: var(--color-faint);
  white-space: nowrap;
}

.vacancyLine {
  display: flex;
  flex-wrap: nowrap;
  align-items: baseline;
  gap: 0.55rem;
  min-width: 0;
}

.vacancy,
.vacancyPlain {
  min-width: 0;
  flex: 1 1 auto;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  font-size: 0.875rem;
  font-weight: 500;
  color: var(--color-muted);
  text-decoration: none;
}

.vacancy {
  transition: color var(--dur) var(--ease);

  @include hover {
    color: var(--color-ink);
  }
}

.status {
  flex: 0 0 auto;
  @include text(mono);
  font-size: 0.6875rem;
  color: var(--color-faint);
}

.why {
  margin: 0;
  max-width: 48rem;
  color: var(--color-faint);
  @include text(dense);
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.done {
  display: inline-flex;
  align-items: center;
  gap: 0.35rem;
  margin-top: 0.15rem;
  cursor: pointer;
  user-select: none;
  white-space: nowrap;
}

.checkbox {
  width: 0.95rem;
  height: 0.95rem;
  accent-color: var(--color-accent-deep);
  cursor: pointer;
}

.doneLabel {
  @include text(mono);
  font-size: 0.6875rem;
  color: var(--color-faint);
}

.empty {
  margin: 0;
  padding: var(--space-7) var(--space-5);
  text-align: center;
  @include text(body);
  color: var(--color-muted);
  background: var(--color-panel);
  border-radius: var(--radius-lg);
}

@include respond-to(tablet) {
  .row {
    grid-template-columns: minmax(0, 1fr);
    gap: 0.75rem;
  }

  .head {
    grid-template-columns: auto minmax(0, 1fr);
    row-gap: 0.3rem;
  }

  .date {
    grid-column: 2;
  }

  .done {
    margin-top: 0;
  }
}
</style>
