<script setup lang="ts">
/**
 * Компактный тег типа лида.
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
  min-height: 1.5rem;
  padding: 0.1rem 0.45rem;
  border: 0.0625rem solid var(--color-line);
  border-radius: var(--radius-sm);
  background: var(--color-raised);
  color: var(--color-muted);
  @include text(mono);
  font-size: 0.6875rem;
  white-space: nowrap;

  &._reply,
  &._call {
    color: var(--color-warning);
    border-color: var(--color-warning);
    background: var(--color-warning-soft);
  }

  &._interview {
    color: var(--color-success);
    border-color: var(--color-success);
    background: var(--color-success-soft);
  }

  &._test {
    color: var(--rail-test);
    border-color: var(--rail-test);
    background: var(--color-panel);
  }

  &._invite {
    color: var(--color-muted);
    border-color: var(--color-line-strong);
  }

  &._closed {
    color: var(--color-danger);
    border-color: var(--color-danger);
    background: var(--color-danger-soft);
  }
}
</style>
