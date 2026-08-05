<script setup lang="ts">
/**
 * Кнопка: фон на ::after, morph radius на hover.
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
  --size: 2.75rem;

  appearance: none;
  position: relative;
  z-index: 0;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  min-height: var(--size);
  padding: 0 1.35rem;
  border: 0;
  background: transparent;
  cursor: pointer;
  user-select: none;
  isolation: isolate;
  @include text(button);
  transition: color var(--dur) var(--ease), opacity var(--dur) var(--ease);

  &::after {
    content: '';
    position: absolute;
    inset: 0;
    z-index: -1;
    border-radius: var(--radius);
    transition:
      background-color var(--dur) var(--ease),
      border-radius var(--dur) var(--ease),
      border-color var(--dur) var(--ease);
  }

  &._small {
    --size: 2.25rem;
    padding: 0 1rem;
    font-size: 0.75rem;
  }

  &._medium {
    --size: 2.75rem;
  }

  &._fullWidth {
    width: 100%;
  }

  &._primary {
    color: var(--color-accent-text);

    &::after {
      background: var(--color-accent);
    }

    @include hover {
      color: var(--color-accent-text);

      &::after {
        background: var(--color-accent-hover);
        border-radius: var(--radius-hover);
      }
    }

    &:active::after {
      background: var(--color-accent-deep);
    }
  }

  &._ghost {
    color: var(--color-muted);

    &::after {
      background: transparent;
      border: 0.0625rem solid var(--color-line-strong);
    }

    @include hover {
      color: var(--color-ink);

      &::after {
        background: var(--color-raised);
        border-color: var(--color-line-strong);
        border-radius: var(--radius-hover);
      }
    }
  }

  &._danger {
    color: var(--color-danger);

    &::after {
      background: var(--color-danger-soft);
      border: 0.0625rem solid var(--color-danger);
    }
  }

  &._disabled,
  &:disabled {
    opacity: 0.45;
    cursor: not-allowed;

    &::after {
      border-radius: var(--radius) !important;
    }
  }

  &._loading .label {
    opacity: 0.65;
  }
}

.label {
  position: relative;
  display: inline-flex;
  align-items: center;
  gap: 0.5rem;
}
</style>
