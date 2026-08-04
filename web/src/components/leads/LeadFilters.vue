<script setup lang="ts">
import type { FilterKey } from '@/types/report'
import UiTextInput from '@/components/ui/UiTextInput.vue'

defineProps<{
  filter: FilterKey
  query: string
  hideClosed: boolean
  counts: Record<FilterKey, number>
  visibleCount: number
}>()

const emit = defineEmits<{
  'update:filter': [value: FilterKey]
  'update:query': [value: string]
  'update:hideClosed': [value: boolean]
}>()

const filters: Array<[FilterKey, string]> = [
  ['all', 'Все'],
  ['reply', 'Ответить'],
  ['call', 'Связаться'],
  ['interview', 'Собес'],
  ['test', 'Тесты'],
  ['invites', 'Приглашения'],
  ['closed', 'Закрытые'],
]
</script>

<template>
  <div :class="$style.leadFilters">
    <div :class="$style.tabs">
      <button
        v-for="[key, label] in filters"
        :key="key"
        type="button"
        :class="[$style.tab, filter === key && $style._active]"
        @click="emit('update:filter', key)"
      >
        {{ label }} · {{ counts[key] }}
      </button>
    </div>
    <div :class="$style.controls">
      <UiTextInput
        :model-value="query"
        placeholder="Поиск: компания, вакансия, фрагмент…"
        @update:model-value="emit('update:query', $event)"
      />
      <label :class="$style.check">
        <input
          type="checkbox"
          :checked="hideClosed"
          @change="emit('update:hideClosed', ($event.target as HTMLInputElement).checked)"
        />
        Скрыть закрытые
      </label>
      <span :class="$style.count">Показано {{ visibleCount }}</span>
    </div>
  </div>
</template>

<style module lang="scss">
.leadFilters {
  display: grid;
  gap: 0.85rem;
}

.tabs {
  display: flex;
  flex-wrap: wrap;
  gap: 0.4rem;
}

.tab {
  appearance: none;
  border: 0.0625rem solid var(--color-border);
  background: #fff;
  border-radius: 999px;
  padding: 0.35rem 0.75rem;
  cursor: pointer;
  color: var(--color-muted);
  font-size: 0.85rem;

  &._active {
    background: var(--color-accent);
    border-color: var(--color-accent);
    color: #fff;
  }
}

.controls {
  display: grid;
  gap: 0.75rem;
  align-items: center;

  @media (min-width: 48rem) {
    grid-template-columns: 1fr auto auto;
  }
}

.check {
  display: inline-flex;
  gap: 0.4rem;
  align-items: center;
  color: var(--color-muted);
  font-size: 0.9rem;
}

.count {
  color: var(--color-muted);
  font-size: 0.85rem;
}
</style>
