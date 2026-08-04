<script setup lang="ts">
defineProps<{
  value: string
  label: string
  tone?: 'default' | 'warning' | 'danger' | 'success'
}>()
</script>

<template>
  <div :class="[$style.statCard, tone && $style[`_${tone}`]]">
    <div :class="$style.value">{{ value }}</div>
    <div :class="$style.label">{{ label }}</div>
  </div>
</template>

<style module lang="scss">
.statCard {
  background: var(--color-surface);
  border: 0.0625rem solid var(--color-border);
  border-radius: var(--radius);
  padding: 0.9rem 1rem;

  &._warning .value {
    color: var(--color-warning);
  }

  &._danger .value {
    color: var(--color-danger);
  }

  &._success .value {
    color: var(--color-success);
  }
}

.value {
  font-family: var(--font-display);
  font-size: 1.75rem;
  line-height: 1.1;
}

.label {
  margin-top: 0.35rem;
  color: var(--color-muted);
  font-size: 0.875rem;
}
</style>
