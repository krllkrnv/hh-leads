<script setup lang="ts">
withDefaults(
  defineProps<{
    label?: string
    type?: 'button' | 'submit'
    variant?: 'primary' | 'ghost' | 'danger'
    disabled?: boolean
  }>(),
  {
    label: '',
    type: 'button',
    variant: 'primary',
    disabled: false,
  },
)

defineEmits<{
  click: [event: MouseEvent]
}>()
</script>

<template>
  <button
    :type="type"
    :class="[$style.uiButton, $style[`_${variant}`]]"
    :disabled="disabled"
    @click="$emit('click', $event)"
  >
    <slot>{{ label }}</slot>
  </button>
</template>

<style module lang="scss">
.uiButton {
  appearance: none;
  border: 0.0625rem solid transparent;
  border-radius: 0.5rem;
  padding: 0.55rem 1rem;
  cursor: pointer;
  font-weight: 600;
  transition: opacity 0.15s ease;

  &:disabled {
    opacity: 0.5;
    cursor: not-allowed;
  }

  &._primary {
    background: var(--color-accent);
    color: #fff;
  }

  &._ghost {
    background: transparent;
    border-color: var(--color-border);
    color: var(--color-text);
  }

  &._danger {
    background: #fff;
    border-color: #fecaca;
    color: var(--color-danger);
  }
}
</style>
