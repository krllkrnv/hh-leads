<script setup lang="ts">
/**
 * Поле ввода: raised fill, soft border on focus.
 */
import { computed, useCssModule } from 'vue'

const props = withDefaults(
  defineProps<{
    modelValue: string
    placeholder?: string
    type?: string
    disabled?: boolean
    invalid?: boolean
    min?: string | number
    max?: string | number
  }>(),
  {
    placeholder: '',
    type: 'text',
    disabled: false,
    invalid: false,
    min: undefined,
    max: undefined,
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
    :min="min"
    :max="max"
    :aria-invalid="invalid || undefined"
    @input="handleInput"
    @focus="emit('focus', $event)"
    @blur="emit('blur', $event)"
  />
</template>

<style module lang="scss">
.UiTextInput {
  width: 100%;
  min-height: 3rem;
  padding: 0.7rem 1rem;
  border: 0.0625rem solid transparent;
  border-radius: var(--radius);
  background: var(--color-raised);
  color: var(--color-ink);
  font-size: 0.875rem;
  font-weight: 500;
  line-height: 1.15;
  letter-spacing: 0.005em;
  transition: border-color var(--dur) var(--ease);

  &::placeholder {
    color: var(--color-muted);
    font-weight: 400;
  }

  @include hover {
    border-color: var(--color-line);
  }

  &:focus {
    outline: none;
    border-color: var(--color-line-strong);
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
