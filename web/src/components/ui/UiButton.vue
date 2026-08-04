<script setup lang="ts">
/**
 * Кнопка UI-kit: primary / ghost / danger, размеры, loading.
 */
import { computed, useCssModule } from 'vue'
import { EButtonSize, EButtonVariant } from '@/types/report'

const props = withDefaults(
  defineProps<{
    label?: string
    type?: 'button' | 'submit'
    variant?: `${EButtonVariant}`
    size?: `${EButtonSize}`
    disabled?: boolean
    loading?: boolean
    fullWidth?: boolean
  }>(),
  {
    label: '',
    type: 'button',
    variant: EButtonVariant.Primary,
    size: EButtonSize.Medium,
    disabled: false,
    loading: false,
    fullWidth: false,
  },
)

const emit = defineEmits<{
  click: [event: MouseEvent]
}>()

const $style = useCssModule()

const classList = computed(() => [
  $style.UiButton,
  {
    [$style[`_${props.variant}`]]: Boolean(props.variant),
    [$style[`_${props.size}`]]: Boolean(props.size),
    [$style._disabled]: props.disabled || props.loading,
    [$style._loading]: props.loading,
    [$style._fullWidth]: props.fullWidth,
  },
])

/**
 * Эмитит click, если кнопка активна.
 */
function handleClick(event: MouseEvent): void {
  if (props.disabled || props.loading) {
    event.preventDefault()
    return
  }
  emit('click', event)
}
</script>

<template>
  <button
    :type="type"
    :class="classList"
    :disabled="disabled || loading"
    :aria-busy="loading || undefined"
    @click="handleClick"
  >
    <span :class="$style.label">
      <slot>{{ label }}</slot>
    </span>
  </button>
</template>

<style module lang="scss">
.UiButton {
  --size: 2.875rem;

  appearance: none;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  min-height: var(--size);
  padding: 0 1.25rem;
  border: 0.0625rem solid transparent;
  border-radius: var(--radius);
  cursor: pointer;
  @include text(button);
  transition:
    background-color var(--dur) var(--ease),
    border-color var(--dur) var(--ease),
    color var(--dur) var(--ease),
    opacity var(--dur) var(--ease);

  &._small {
    --size: 2.25rem;
    padding: 0 0.9rem;
    font-size: 0.8125rem;
  }

  &._medium {
    --size: 2.875rem;
  }

  &._fullWidth {
    width: 100%;
  }

  &._primary {
    background: var(--color-accent);
    color: var(--color-accent-text);

    &:hover:not(:disabled) {
      background: var(--color-accent-hover);
    }
  }

  &._ghost {
    background: transparent;
    border-color: var(--color-line);
    color: var(--color-ink);

    &:hover:not(:disabled) {
      border-color: var(--color-accent);
      color: var(--color-accent);
      background: var(--color-accent-soft);
    }
  }

  &._danger {
    background: var(--color-danger-soft);
    border-color: var(--color-danger);
    color: var(--color-danger);
  }

  &._disabled,
  &:disabled {
    opacity: 0.42;
    cursor: not-allowed;
  }

  &._loading .label {
    opacity: 0.65;
  }
}

.label {
  display: inline-flex;
  align-items: center;
  gap: 0.4rem;
}
</style>
