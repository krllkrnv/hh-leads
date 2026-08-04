<script setup lang="ts">
/**
 * Метрика сводки: крупное mono-значение + подпись.
 */
import { computed, useCssModule } from 'vue'
import { EStatTone } from '@/types/report'

const props = withDefaults(
  defineProps<{
    value: string
    label: string
    tone?: `${EStatTone}`
  }>(),
  {
    tone: EStatTone.Default,
  },
)

const $style = useCssModule()

const classList = computed(() => [$style.StatCard, $style[`_${props.tone}`]])
</script>

<template>
  <div :class="classList">
    <div :class="$style.value">{{ value }}</div>
    <div :class="$style.label">{{ label }}</div>
  </div>
</template>

<style module lang="scss">
.StatCard {
  display: grid;
  gap: 0.45rem;
  min-width: 0;

  &._warning .value {
    color: var(--color-warning);
  }

  &._danger .value {
    color: var(--color-danger);
  }

  &._success .value {
    color: var(--color-success);
  }

  &._default .value {
    color: var(--color-ink);
  }
}

.value {
  @include text(mono-lg);
}

.label {
  @include text(caption);
  color: var(--color-muted);
}
</style>
