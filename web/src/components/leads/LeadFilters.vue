<script setup lang="ts">
/**
 * Очереди лидов, быстрый поиск и пресеты профиля (стек, грейд, роль).
 */
import { ref } from 'vue'
import type { FilterKey } from '@/types/report'
import { EFilterKey, FILTER_LABELS } from '@/types/report'
import type { ProfilePreset } from '@/lib/profilePresets'
import { PROFILE_GROUPS } from '@/lib/profilePresets'
import UiTextInput from '@/components/ui/UiTextInput.vue'

defineProps<{
  filter: FilterKey
  query: string
  hideClosed: boolean
  includeKeywords: string
  excludeKeywords: string
  counts: Record<FilterKey, number>
  visibleCount: number
}>()

const emit = defineEmits<{
  'update:filter': [value: FilterKey]
  'update:query': [value: string]
  'update:hideClosed': [value: boolean]
  'update:includeKeywords': [value: string]
  'update:excludeKeywords': [value: string]
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

const openGroupId = ref<string | null>(null)
const panelId = 'lead-filters-panel'

/**
 * Переключает, какую очередь лидов сейчас смотрим.
 */
function handleFilter(key: FilterKey): void {
  emit('update:filter', key)
}

/**
 * Перемещает фокус между вкладками очередей стрелками, Home и End.
 */
function onTabKeydown(event: KeyboardEvent, index: number): void {
  let next: number
  switch (event.key) {
    case 'ArrowRight':
    case 'ArrowDown':
      next = (index + 1) % FILTER_ORDER.length
      break
    case 'ArrowLeft':
    case 'ArrowUp':
      next = (index - 1 + FILTER_ORDER.length) % FILTER_ORDER.length
      break
    case 'Home':
      next = 0
      break
    case 'End':
      next = FILTER_ORDER.length - 1
      break
    default:
      return
  }
  event.preventDefault()
  handleFilter(FILTER_ORDER[next])
  const tabs = (event.currentTarget as HTMLElement).parentElement?.querySelectorAll('[role="tab"]')
  const el = tabs?.[next] as HTMLElement | undefined
  el?.focus()
}

/**
 * Включает или выключает скрытие закрытых вакансий в списке.
 */
function onHideClosed(event: Event): void {
  const target = event.target as HTMLInputElement
  emit('update:hideClosed', target.checked)
}

/**
 * По клику открывает или закрывает выпадающий список пресетов группы.
 */
function toggleGroup(id: string): void {
  openGroupId.value = openGroupId.value === id ? null : id
}

/**
 * Открывает выпадающий список пресетов при наведении или фокусе.
 */
function openGroup(id: string): void {
  openGroupId.value = id
}

/**
 * Закрывает выпадающий список пресетов.
 */
function closeGroup(): void {
  openGroupId.value = null
}

/**
 * Подставляет слова пресета в поля «Содержит» и «Исключить».
 */
function applyPreset(preset: ProfilePreset): void {
  emit('update:includeKeywords', preset.include)
  emit('update:excludeKeywords', preset.exclude ?? '')
  closeGroup()
}

/**
 * Очищает поля фильтра профиля.
 */
function clearProfile(): void {
  emit('update:includeKeywords', '')
  emit('update:excludeKeywords', '')
}

function onPresetKeydown(event: KeyboardEvent): void {
  if (event.key === 'Escape') {
    closeGroup()
  }
}
</script>

<template>
  <div :class="$style.LeadFilters">
    <div :class="$style.tabsShell" role="tablist" aria-label="Очереди лидов">
      <button
        v-for="(key, index) in FILTER_ORDER"
        :id="`lead-tab-${key}`"
        :key="key"
        type="button"
        role="tab"
        :aria-selected="filter === key"
        :aria-controls="panelId"
        :tabindex="filter === key ? 0 : -1"
        :class="[$style.tab, filter === key && $style._active]"
        @click="handleFilter(key)"
        @keydown="onTabKeydown($event, index)"
      >
        <span :class="$style.tabLabel">{{ FILTER_LABELS[key] }}</span>
        <span :class="$style.tabCount">{{ counts[key] }}</span>
      </button>
    </div>

    <div :id="panelId" role="tabpanel" :aria-labelledby="`lead-tab-${filter}`" :class="$style.profile">
      <div :class="$style.profileFields">
        <label :class="$style.field">
          <span :class="$style.fieldLabel">В названии вакансии или компании есть</span>
          <UiTextInput
            :model-value="includeKeywords"
            placeholder="Например: python, django — все слова должны встретиться"
            @update:model-value="emit('update:includeKeywords', $event)"
          />
        </label>
        <label :class="$style.field">
          <span :class="$style.fieldLabel">Исключить вакансии со словами</span>
          <UiTextInput
            :model-value="excludeKeywords"
            placeholder="Например: битрикс, php"
            @update:model-value="emit('update:excludeKeywords', $event)"
          />
        </label>
      </div>

      <div :class="$style.presetsBlock" @keydown="onPresetKeydown">
        <div :class="$style.presetsHead">
          <span :class="$style.fieldLabel">Готовые наборы слов</span>
          <button type="button" :class="$style.clearBtn" @click="clearProfile">Очистить фильтр</button>
        </div>

        <div :class="$style.groups" @mouseleave="closeGroup">
          <div
            v-for="group in PROFILE_GROUPS"
            :key="group.id"
            :class="[$style.group, openGroupId === group.id && $style._open]"
            @mouseenter="openGroup(group.id)"
            @focusin="openGroup(group.id)"
          >
            <button
              type="button"
              :class="$style.groupBtn"
              :aria-expanded="openGroupId === group.id"
              :aria-haspopup="true"
              @click="toggleGroup(group.id)"
            >
              {{ group.label }}
              <span :class="$style.groupCount">{{ group.presets.length }}</span>
            </button>

            <div v-show="openGroupId === group.id" :class="$style.menu" role="menu">
              <button
                v-for="preset in group.presets"
                :key="preset.label"
                type="button"
                role="menuitem"
                :class="$style.menuItem"
                :title="
                  [preset.include, preset.exclude ? `исключить: ${preset.exclude}` : '']
                    .filter(Boolean)
                    .join(' · ')
                "
                @click="applyPreset(preset)"
              >
                <span :class="$style.menuLabel">{{ preset.label }}</span>
                <span :class="$style.menuMeta">{{ preset.include }}</span>
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>

    <div :class="$style.controls">
      <UiTextInput
        :model-value="query"
        placeholder="Поиск по компании или названию вакансии"
        @update:model-value="emit('update:query', $event)"
      />
      <label :class="$style.check">
        <input
          :class="$style.checkbox"
          type="checkbox"
          :checked="hideClosed"
          @change="onHideClosed"
        />
        <span :class="$style.checkLabel">Скрыть закрытые вакансии</span>
      </label>
      <span :class="$style.visible">
        {{ visibleCount }}
        <span :class="$style.visibleMuted">сейчас в списке</span>
      </span>
    </div>
  </div>
</template>

<style module lang="scss">
.LeadFilters {
  display: grid;
  gap: var(--space-4);
}

.tabsShell {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 0.2rem;
  padding: 0.25rem;
  background: var(--color-panel);
  border-radius: var(--radius-lg);
}

.tab {
  appearance: none;
  display: inline-flex;
  align-items: center;
  gap: 0.35rem;
  min-height: 2.25rem;
  padding: 0.35rem 0.75rem;
  border: 0;
  border-radius: calc(var(--radius) - 0.05rem);
  background: transparent;
  cursor: pointer;
  color: var(--color-faint);
  transition:
    color var(--dur) var(--ease),
    background-color var(--dur) var(--ease);

  @include hover {
    color: var(--color-ink);
    background: var(--color-raised);
  }

  &._active {
    color: var(--color-accent-text);
    background: var(--color-accent);

    .tabCount {
      color: var(--color-accent-text);
      opacity: 0.72;
    }
  }
}

.tabLabel {
  @include text(caption);
  font-weight: 600;
  line-height: 1;
}

.tabCount {
  @include text(mono);
  font-size: 0.75rem;
  line-height: 1;
  color: var(--color-faint);
}

.profile {
  display: grid;
  gap: var(--space-4);
  padding: var(--space-5);
  background: var(--color-panel);
  border-radius: var(--radius-lg);
}

.profileFields {
  display: grid;
  gap: var(--space-3);

  @include respond-to(from-desktop) {
    grid-template-columns: 1fr 1fr;
  }
}

.field {
  display: grid;
  gap: 0.4rem;
}

.fieldLabel {
  @include text(label);
  color: var(--color-faint);
}

.presetsBlock {
  display: grid;
  gap: var(--space-2);
}

.presetsHead {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: var(--space-3);
}

.clearBtn {
  appearance: none;
  border: 0;
  background: transparent;
  color: var(--color-faint);
  @include text(caption);
  cursor: pointer;
  padding: 0;

  @include hover {
    color: var(--color-accent);
  }
}

.groups {
  display: flex;
  flex-wrap: wrap;
  gap: 0.4rem;
}

.group {
  position: relative;
}

.groupBtn {
  appearance: none;
  display: inline-flex;
  align-items: center;
  gap: 0.4rem;
  border: 0;
  border-radius: var(--radius);
  background: var(--color-raised);
  color: var(--color-muted);
  padding: 0.45rem 0.8rem;
  @include text(caption);
  font-weight: 600;
  cursor: pointer;
  transition:
    color var(--dur) var(--ease),
    background-color var(--dur) var(--ease),
    border-radius var(--dur) var(--ease);

  .group:hover &,
  .group._open & {
    color: var(--color-ink);
    background: var(--color-accent-soft);
    border-radius: var(--radius-hover);
  }
}

.groupCount {
  @include text(mono);
  font-size: 0.6875rem;
  color: var(--color-faint);
}

.menu {
  position: absolute;
  top: calc(100% + 0.35rem);
  left: 0;
  z-index: 20;
  min-width: 16rem;
  max-width: min(22rem, 80vw);
  max-height: 18rem;
  overflow: auto;
  padding: 0.4rem;
  border-radius: var(--radius-lg);
  background: var(--color-raised);
  box-shadow: 0 0.75rem 2rem rgb(0 0 0 / 35%);
}

.menuItem {
  appearance: none;
  width: 100%;
  display: grid;
  gap: 0.15rem;
  text-align: left;
  border: 0;
  border-radius: var(--radius);
  background: transparent;
  color: var(--color-ink);
  padding: 0.55rem 0.7rem;
  cursor: pointer;

  @include hover {
    background: var(--color-panel);
  }
}

.menuLabel {
  @include text(caption);
  font-weight: 600;
}

.menuMeta {
  @include text(mono);
  font-size: 0.6875rem;
  color: var(--color-faint);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.controls {
  display: grid;
  gap: var(--space-3);
  align-items: center;
  padding: var(--space-4) var(--space-5);
  background: var(--color-panel);
  border-radius: var(--radius-lg);

  @include respond-to(from-desktop) {
    grid-template-columns: 1fr auto auto;
  }
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
  accent-color: var(--color-accent-deep);
}

.checkLabel {
  @include text(caption);
  color: var(--color-muted);
}

.visible {
  @include text(mono);
  font-weight: 600;
  color: var(--color-ink);
  white-space: nowrap;
}

.visibleMuted {
  font-weight: 500;
  color: var(--color-faint);
}
</style>
