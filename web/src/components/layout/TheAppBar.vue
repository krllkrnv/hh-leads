<script setup lang="ts">
/**
 * Шапка с названием приложения и действиями по текущему отчёту.
 */
import { onBeforeUnmount, onMounted, ref } from 'vue'
import BrandTitle from '@/components/ui/BrandTitle.vue'
import UiButton from '@/components/ui/UiButton.vue'
import { EButtonSize, EButtonVariant } from '@/types/report'

defineProps<{
  subtitle?: string
  showActions?: boolean
  loading?: boolean
}>()

const emit = defineEmits<{
  export: [format: 'json' | 'xlsx']
  refresh: []
  reset: []
}>()

const downloadOpen = ref(false)
const downloadRoot = ref<HTMLElement | null>(null)

function toggleDownload(): void {
  downloadOpen.value = !downloadOpen.value
}

function chooseFormat(format: 'json' | 'xlsx'): void {
  downloadOpen.value = false
  emit('export', format)
}

function onDocumentClick(event: MouseEvent): void {
  const root = downloadRoot.value
  if (!root || !(event.target instanceof Node) || root.contains(event.target)) {
    return
  }
  downloadOpen.value = false
}

function onDocumentKeydown(event: KeyboardEvent): void {
  if (event.key === 'Escape') {
    downloadOpen.value = false
  }
}

onMounted(() => {
  document.addEventListener('click', onDocumentClick)
  document.addEventListener('keydown', onDocumentKeydown)
})

onBeforeUnmount(() => {
  document.removeEventListener('click', onDocumentClick)
  document.removeEventListener('keydown', onDocumentKeydown)
})
</script>

<template>
  <header :class="$style.TheAppBar">
    <div :class="$style.inner">
      <div :class="$style.brandBlock">
        <BrandTitle size="h1" />
        <p v-if="subtitle" :class="$style.subtitle">{{ subtitle }}</p>
      </div>
      <div v-if="showActions" :class="$style.actions">
        <div ref="downloadRoot" :class="$style.download">
          <UiButton
            :variant="EButtonVariant.Ghost"
            :size="EButtonSize.Small"
            :disabled="loading"
            :aria-expanded="downloadOpen"
            aria-haspopup="menu"
            @click="toggleDownload"
          >
            Скачать
          </UiButton>
          <div
            v-show="downloadOpen"
            :class="$style.menu"
            role="menu"
            aria-label="Формат файла"
          >
            <button
              type="button"
              role="menuitem"
              :class="$style.menuItem"
              @click="chooseFormat('json')"
            >
              JSON
              <span :class="$style.menuHint">удобно открыть снова в дашборде</span>
            </button>
            <button
              type="button"
              role="menuitem"
              :class="$style.menuItem"
              @click="chooseFormat('xlsx')"
            >
              Excel
              <span :class="$style.menuHint">таблица для Excel или Google Sheets</span>
            </button>
          </div>
        </div>
        <UiButton
          :variant="EButtonVariant.Ghost"
          :size="EButtonSize.Small"
          :disabled="loading"
          @click="emit('refresh')"
        >
          Загрузить заново
        </UiButton>
        <UiButton
          :variant="EButtonVariant.Ghost"
          :size="EButtonSize.Small"
          :disabled="loading"
          @click="emit('reset')"
        >
          Сбросить отчёт
        </UiButton>
      </div>
    </div>
  </header>
</template>

<style module lang="scss">
.TheAppBar {
  position: sticky;
  top: 0;
  z-index: 30;
  margin: var(--space-4) 0 0;
  padding: 0 0 var(--space-3);
}

.inner {
  display: flex;
  flex-wrap: wrap;
  justify-content: space-between;
  align-items: center;
  gap: var(--space-4);
  min-height: var(--header-h);
  padding: 0.85rem 1.25rem;
  background: var(--color-panel);
  border-radius: var(--radius-lg);
}

.brandBlock {
  display: grid;
  gap: 0.2rem;
  min-width: 0;
}

.subtitle {
  margin: 0;
  @include text(caption);
  color: var(--color-faint);
}

.actions {
  display: flex;
  flex-wrap: wrap;
  gap: var(--space-2);
}

.download {
  position: relative;
}

.menu {
  position: absolute;
  top: calc(100% + 0.35rem);
  right: 0;
  z-index: 40;
  min-width: 14rem;
  padding: 0.35rem;
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
  @include text(caption);
  font-weight: 600;

  @include hover {
    background: var(--color-panel);
  }
}

.menuHint {
  @include text(mono);
  font-size: 0.6875rem;
  font-weight: 500;
  color: var(--color-faint);
}
</style>
