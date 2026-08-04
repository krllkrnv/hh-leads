<script setup lang="ts">
/**
 * Wordmark HHLeads: HH красным, Leads основным цветом.
 */
withDefaults(
  defineProps<{
    tag?: 'h1' | 'p' | 'span'
    size?: 'display' | 'h1'
  }>(),
  {
    tag: 'h1',
    size: 'display',
  },
)
</script>

<template>
  <component
    :is="tag"
    :class="[$style.BrandTitle, $style[`_${size}`]]"
  >
    <span :class="$style.hh">HH</span><span :class="$style.rest">Leads</span>
  </component>
</template>

<style module lang="scss">
.BrandTitle {
  margin: 0;
  color: var(--color-ink);

  &._display {
    @include text(display);
  }

  &._h1 {
    @include text(h1);
  }
}

.hh {
  color: var(--color-hh);
}

.rest {
  color: inherit;
}
</style>
