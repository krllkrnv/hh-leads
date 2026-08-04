<script setup lang="ts">
/**
 * Шапка: wordmark + обновление / экспорт / сброс.
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
        Сменить данные
      </UiButton>
    </div>
  </header>
</template>

<style module lang="scss">
.TheAppBar {
  display: flex;
  flex-wrap: wrap;
  justify-content: space-between;
  align-items: end;
  gap: var(--space-4);
  min-height: var(--header-h);
  padding: var(--space-4) 0;
  border-bottom: 0.0625rem solid var(--color-line);
}

.brandBlock {
  display: grid;
  gap: 0.35rem;
}

.subtitle {
  margin: 0;
  @include text(caption);
  color: var(--color-muted);
}

.actions {
  display: flex;
  flex-wrap: wrap;
  gap: var(--space-2);
}
</style>
