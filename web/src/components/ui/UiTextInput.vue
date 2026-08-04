<script setup lang="ts">
defineProps<{
  modelValue: string
  placeholder?: string
  type?: string
}>()

defineEmits<{
  'update:modelValue': [value: string]
}>()
</script>

<template>
  <input
    :class="$style.uiTextInput"
    :type="type || 'text'"
    :value="modelValue"
    :placeholder="placeholder"
    @input="$emit('update:modelValue', ($event.target as HTMLInputElement).value)"
  />
</template>

<style module lang="scss">
.uiTextInput {
  width: 100%;
  border: 0.0625rem solid var(--color-border);
  border-radius: 0.5rem;
  background: #fff;
  padding: 0.65rem 0.8rem;
  color: var(--color-text);

  &:focus {
    outline: 0.125rem solid rgba(15, 118, 110, 0.35);
    border-color: var(--color-accent);
  }
}
</style>
