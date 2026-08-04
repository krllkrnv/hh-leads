<script setup lang="ts">
/**
 * Фильтры очередей, поиск и переключатель закрытых.
 */
import type { FilterKey } from '@/types/report'
import {
  EFilterKey,
  FILTER_LABELS,
} from '@/types/report'
import UiTextInput from '@/components/ui/UiTextInput.vue'

defineProps<{
  filter: FilterKey
  query: string
  hideClosed: boolean
  frontendOnly: boolean
  counts: Record<FilterKey, number>
  visibleCount: number
}>()

const emit = defineEmits<{
  'update:filter': [value: FilterKey]
  'update:query': [value: string]
  'update:hideClosed': [value: boolean]
  'update:frontendOnly': [value: boolean]
}>()

const FILTER_ORDER: FilterKey[] = [
  EFilterKey.All,
  EFilterKey.Reply,
  EFilterKey.Call,
  EFilterKey.Interview,
  EFilterKey.Test,
  EFilterKey.Invites,
  EFilterKey.Wait,
  EFilterKey.Bot,
  EFilterKey.Closed,
]

/**
 * Переключает активную очередь.
 */
function handleFilter(key: FilterKey): void {
  emit('update:filter', key)
}

/**
 * Обновляет строку поиска.
 */
function onQuery(value: string): void {
  emit('update:query', value)
}

/**
 * Переключает скрытие закрытых лидов.
 */
function onHideClosed(event: Event): void {
  const target = event.target as HTMLInputElement
  emit('update:hideClosed', target.checked)
}

/**
 * Переключает фильтр frontend-вакансий.
 */
function onFrontendOnly(event: Event): void {
  const target = event.target as HTMLInputElement
  emit('update:frontendOnly', target.checked)
}
</script>

<template>
  <div :class="$style.LeadFilters">
    <div :class="$style.tabs" role="tablist" aria-label="Очереди">
      <button
        v-for="key in FILTER_ORDER"
        :key="key"
        type="button"
        role="tab"
        :aria-selected="filter === key"
        :class="[$style.tab, filter === key && $style._active]"
        @click="handleFilter(key)"
      >
        <span :class="$style.tabLabel">{{ FILTER_LABELS[key] }}</span>
        <span :class="$style.tabCount">{{ counts[key] }}</span>
      </button>
    </div>

    <div :class="$style.controls">
      <UiTextInput
        :model-value="query"
        placeholder="Компания, вакансия, фрагмент…"
        @update:model-value="onQuery"
      />
      <div :class="$style.toggles">
        <label :class="$style.check">
          <input
            :class="$style.checkbox"
            type="checkbox"
            :checked="hideClosed"
            @change="onHideClosed"
          />
          <span :class="$style.checkLabel">Скрыть закрытые</span>
        </label>
        <label :class="$style.check">
          <input
            :class="$style.checkbox"
            type="checkbox"
            :checked="frontendOnly"
            @change="onFrontendOnly"
          />
          <span :class="$style.checkLabel">Только frontend</span>
        </label>
      </div>
      <span :class="$style.visible">
        показано
        <span :class="$style.visibleNum">{{ visibleCount }}</span>
      </span>
    </div>
  </div>
</template>

<style module lang="scss">
.LeadFilters {
  display: grid;
  gap: var(--space-4);
  position: sticky;
  top: 0;
  z-index: 5;
  padding: var(--space-4) 0;
  background: color-mix(in srgb, var(--color-bg) 92%, transparent);
  backdrop-filter: blur(0.5rem);
}

.tabs {
  display: flex;
  flex-wrap: wrap;
  gap: 0;
  border-bottom: 0.0625rem solid var(--color-line);
}

.tab {
  appearance: none;
  position: relative;
  display: inline-flex;
  align-items: baseline;
  gap: 0.45rem;
  min-height: 2.75rem;
  padding: 0.5rem 0.85rem;
  border: 0;
  background: transparent;
  cursor: pointer;
  color: var(--color-muted);
  transition: color var(--dur) var(--ease);

  &::after {
    content: '';
    position: absolute;
    left: 0.85rem;
    right: 0.85rem;
    bottom: -0.0625rem;
    height: 0.125rem;
    background: transparent;
    transition: background-color var(--dur) var(--ease);
  }

  &:hover {
    color: var(--color-ink);
  }

  &._active {
    color: var(--color-ink);

    &::after {
      background: var(--color-accent);
    }

    .tabCount {
      color: var(--color-accent);
    }
  }
}

.tabLabel {
  @include text(caption);
  font-weight: 600;
}

.tabCount {
  @include text(mono);
  color: var(--color-faint);
}

.controls {
  display: grid;
  gap: var(--space-3);
  align-items: center;

  @include respond-to(from-desktop) {
    grid-template-columns: 1fr auto auto;
  }
}

.toggles {
  display: flex;
  flex-wrap: wrap;
  gap: 0.75rem 1.25rem;
  align-items: center;
}

.check {
  display: inline-flex;
  gap: 0.5rem;
  align-items: center;
  cursor: pointer;
  user-select: none;
}

.checkbox {
  width: 1rem;
  height: 1rem;
  accent-color: var(--color-accent);
}

.checkLabel {
  @include text(caption);
  color: var(--color-muted);
}

.visible {
  @include text(mono);
  color: var(--color-faint);
}

.visibleNum {
  color: var(--color-ink);
  font-weight: 600;
}
</style>
