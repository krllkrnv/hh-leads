<script setup lang="ts">
import type { LeadTag } from '@/types/report'

const props = defineProps<{
  tag: LeadTag
  active?: boolean
}>()

const labels: Record<LeadTag, string> = {
  reply: 'ответить',
  call: 'связаться',
  interview: 'собес',
  test: 'тест',
  invite: 'приглашение',
  closed: 'закрыто',
}
</script>

<template>
  <span
    :class="[
      $style.uiPill,
      $style[`_${props.tag}`],
      props.active && $style._active,
    ]"
  >
    {{ labels[props.tag] }}
  </span>
</template>

<style module lang="scss">
.uiPill {
  display: inline-flex;
  align-items: center;
  padding: 0.15rem 0.55rem;
  border-radius: 999px;
  font-size: 0.75rem;
  font-weight: 600;
  background: #f5f5f4;
  color: var(--color-muted);
  border: 0.0625rem solid var(--color-border);

  &._active {
    outline: 0.125rem solid rgba(15, 118, 110, 0.25);
  }

  &._reply,
  &._call {
    background: #fff7ed;
    color: var(--color-warning);
    border-color: #fed7aa;
  }

  &._interview {
    background: #ecfdf5;
    color: var(--color-success);
    border-color: #a7f3d0;
  }

  &._test {
    background: var(--color-accent-soft);
    color: var(--color-accent);
    border-color: #99f6e4;
  }

  &._closed {
    background: #fef2f2;
    color: var(--color-danger);
    border-color: #fecaca;
  }
}
</style>
