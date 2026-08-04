<script setup lang="ts">
/**
 * Текстовое поле UI-kit с v-model.
 */
import { computed, useCssModule } from 'vue'

const props = withDefaults(
  defineProps<{
    modelValue: string
    placeholder?: string
    type?: string
    disabled?: boolean
    invalid?: boolean
  }>(),
  {
    placeholder: '',
    type: 'text',
    disabled: false,
    invalid: false,
  },
)

const emit = defineEmits<{
  'update:modelValue': [value: string]
  focus: [event: FocusEvent]
  blur: [event: FocusEvent]
}>()

const $style = useCssModule()

const classList = computed(() => [
  $style.UiTextInput,
  {
    [$style._invalid]: props.invalid,
    [$style._disabled]: props.disabled,
  },
])

/**
 * Пробрасывает значение инпута в v-model.
 */
function handleInput(event: Event): void {
  const target = event.target as HTMLInputElement
  emit('update:modelValue', target.value)
}
</script>

<template>
  <input
    :class="classList"
    :type="type"
    :value="modelValue"
    :placeholder="placeholder"
    :disabled="disabled"
    :aria-invalid="invalid || undefined"
    @input="handleInput"
    @focus="emit('focus', $event)"
    @blur="emit('blur', $event)"
  />
</template>

<style module lang="scss">
.UiTextInput {
  width: 100%;
  min-height: 2.875rem;
  padding: 0.55rem 0.85rem;
  border: 0.0625rem solid var(--color-line);
  border-radius: var(--radius);
  background: var(--color-raised);
  color: var(--color-ink);
  transition: border-color var(--dur) var(--ease);

  &::placeholder {
    color: var(--color-faint);
  }

  &:hover:not(:disabled) {
    border-color: var(--color-line-strong);
  }

  &:focus {
    outline: none;
    border-color: var(--color-accent);
    box-shadow: var(--shadow-focus);
  }

  &._invalid {
    border-color: var(--color-danger);
  }

  &._disabled,
  &:disabled {
    opacity: 0.5;
    cursor: not-allowed;
  }
}
</style>
