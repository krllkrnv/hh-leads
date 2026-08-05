<script setup lang="ts">
/**
 * Цветная плашка типа лида: у каждого тега свой оттенок.
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
  font-weight: 600;
  user-select: none;
  white-space: nowrap;

  /* Нужен ответ — красный, срочно */
  &._reply {
    color: var(--color-tag-reply);
    background: var(--color-tag-reply-soft);
  }

  /* Связаться — янтарный, контакт */
  &._call {
    color: var(--color-tag-call);
    background: var(--color-tag-call-soft);
  }

  /* Собеседование — зелёный */
  &._interview {
    color: var(--color-tag-interview);
    background: var(--color-tag-interview-soft);
  }

  /* Тестовое — голубой */
  &._test {
    color: var(--color-tag-test);
    background: var(--color-tag-test-soft);
  }

  /* Приглашение — фиолетовый */
  &._invite {
    color: var(--color-tag-invite);
    background: var(--color-tag-invite-soft);
  }

  /* Ожидание — серо-голубой */
  &._wait {
    color: var(--color-tag-wait);
    background: var(--color-tag-wait-soft);
  }

  /* Автоответ — нейтральный серый */
  &._bot {
    color: var(--color-tag-bot);
    background: var(--color-tag-bot-soft);
  }

  /* Обсуждение — приглушённый */
  &._discuss {
    color: var(--color-tag-discuss);
    background: var(--color-tag-discuss-soft);
  }

  /* Закрыто — спокойный серый, не кричит как ошибка */
  &._closed {
    color: var(--color-tag-closed);
    background: var(--color-tag-closed-soft);
  }
}
</style>
