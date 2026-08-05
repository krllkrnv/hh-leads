<script setup lang="ts">
/**
 * Шапка: wordmark и действия отчёта.
 */
import BrandTitle from '@/components/ui/BrandTitle.vue'
import UiButton from '@/components/ui/UiButton.vue'
import { EButtonSize, EButtonVariant } from '@/types/report'

defineProps<{
  subtitle?: string
  showActions?: boolean
  loading?: boolean
}>()

const emit = defineEmits<{
  refresh: []
  export: []
  reset: []
}>()
</script>

<template>
  <header :class="$style.TheAppBar">
    <div :class="$style.inner">
      <div :class="$style.brandBlock">
        <BrandTitle size="h1" />
        <p v-if="subtitle" :class="$style.subtitle">{{ subtitle }}</p>
      </div>
      <div v-if="showActions" :class="$style.actions">
        <UiButton
          :variant="EButtonVariant.Ghost"
          :size="EButtonSize.Small"
          :disabled="loading"
          @click="emit('export')"
        >
          JSON
        </UiButton>
        <UiButton
          :variant="EButtonVariant.Ghost"
          :size="EButtonSize.Small"
          :disabled="loading"
          @click="emit('refresh')"
        >
          Обновить
        </UiButton>
        <UiButton
          :variant="EButtonVariant.Ghost"
          :size="EButtonSize.Small"
          :disabled="loading"
          @click="emit('reset')"
        >
          Сменить
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
  background: var(--color-bg);
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
</style>
