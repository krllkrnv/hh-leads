<script setup lang="ts">
/**
 * Тег типа лида: soft fill.
 */
import { computed, useCssModule } from 'vue'
import type { LeadTag } from '@/types/report'
import { LEAD_TAG_LABELS } from '@/types/report'

const props = defineProps<{
  tag: LeadTag
}>()

const $style = useCssModule()

const classList = computed(() => [$style.UiPill, $style[`_${props.tag}`]])
</script>

<template>
  <span :class="classList">{{ LEAD_TAG_LABELS[tag] }}</span>
</template>

<style module lang="scss">
.UiPill {
  display: inline-flex;
  align-items: center;
  width: fit-content;
  min-height: 1.5rem;
  padding: 0.2rem 0.65rem;
  gap: 0.35rem;
  border: 0.0625rem solid transparent;
  border-radius: var(--radius-sm);
  background: var(--color-raised);
  color: var(--color-muted);
  @include text(caption);
  user-select: none;
  white-space: nowrap;

  &._reply,
  &._call {
    color: var(--color-warning);
    background: var(--color-warning-soft);
  }

  &._interview {
    color: var(--color-success);
    background: var(--color-success-soft);
  }

  &._test {
    color: var(--color-accent);
    background: var(--color-accent-soft);
  }

  &._invite {
    color: var(--color-muted);
    background: var(--color-raised);
  }

  &._wait,
  &._bot,
  &._discuss {
    color: var(--color-faint);
    background: var(--color-raised);
  }

  &._closed {
    color: var(--color-danger);
    background: var(--color-danger-soft);
  }
}
</style>
