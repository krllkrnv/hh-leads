<script setup lang="ts">
/**
 * Панель прогресса синхронизации или разбора файла — в потоке страницы, с анимацией появления.
 */
import { computed, nextTick, ref, watch } from 'vue'
import type { ProgressLogItem } from '@/composables/useProgressLog'
import type { ProgressStage } from '@/types/progress'
import { PROGRESS_STAGES } from '@/types/progress'

const props = defineProps<{
  active: boolean
  mode: 'sync' | 'upload' | null
  stage: ProgressStage | null
  message: string
  current: number
  total: number
  percent: number
  logs: ProgressLogItem[]
}>()

const emit = defineEmits<{
  cancel: []
}>()

const logRef = ref<HTMLElement | null>(null)

const title = computed(() => {
  if (props.mode === 'upload') {
    return 'Разбираю файл отчёта'
  }
  return 'Загружаю чаты с hh'
})

const visibleStages = computed(() => {
  if (props.mode === 'upload') {
    return PROGRESS_STAGES.filter((item) => ['parse', 'classify', 'build'].includes(item.id))
  }
  return PROGRESS_STAGES.filter((item) =>
    ['auth', 'list', 'fetch', 'classify', 'build'].includes(item.id),
  )
})

const stageOrder = computed(() => visibleStages.value.map((item) => item.id))

/**
 * На каком шаге сейчас этап: ещё не начат, активен или уже пройден.
 */
function stageStatus(id: ProgressStage): 'pending' | 'active' | 'done' {
  const order = stageOrder.value
  const thisIdx = order.indexOf(id)
  if (thisIdx < 0) {
    return 'pending'
  }

  const current = props.stage
  if (!current || current === 'start') {
    return thisIdx === 0 ? 'active' : 'pending'
  }
  if (current === 'done') {
    return 'done'
  }

  let currentIdx = order.indexOf(current)
  if (current === 'error' || current === 'warn' || currentIdx < 0) {
    currentIdx = 0
    for (let i = props.logs.length - 1; i >= 0; i -= 1) {
      const idx = order.indexOf(props.logs[i].stage as ProgressStage)
      if (idx >= 0) {
        currentIdx = idx
        break
      }
    }
  }

  if (thisIdx < currentIdx) {
    return 'done'
  }
  if (thisIdx === currentIdx) {
    return 'active'
  }
  return 'pending'
}

watch(
  () => props.logs.length,
  async () => {
    await nextTick()
    const el = logRef.value
    if (el) {
      el.scrollTop = el.scrollHeight
    }
  },
)
</script>

<template>
  <Transition name="progress-expand">
    <div v-if="active" :class="$style.shell">
      <div :class="$style.shellInner">
        <section
          :class="$style.LiveProgressPanel"
          role="status"
          aria-live="polite"
          aria-busy="true"
        >
          <div :class="$style.barTrack" aria-hidden="true">
            <div
              :class="$style.barFill"
              :style="{ width: `${Math.max(percent, total ? 4 : 12)}%` }"
            />
          </div>

          <header :class="$style.header">
            <div :class="$style.pulseWrap" aria-hidden="true">
              <span :class="$style.pulseCore" />
              <span :class="$style.pulseRing" />
            </div>
            <div :class="$style.copy">
              <h2 :class="$style.title">{{ title }}</h2>
              <p :class="$style.message">{{ message || 'Ещё готовлюсь…' }}</p>
            </div>
            <div :class="$style.headerAside">
              <div v-if="total > 0" :class="$style.counter">
                <span :class="$style.counterValue">{{ current }}</span>
                <span :class="$style.counterSep">/</span>
                <span>{{ total }}</span>
              </div>
              <button
                v-if="mode === 'sync' || mode === 'upload'"
                type="button"
                :class="$style.cancelBtn"
                @click="emit('cancel')"
              >
                Остановить
              </button>
            </div>
          </header>

          <ol :class="$style.stages">
            <li
              v-for="item in visibleStages"
              :key="item.id"
              :class="[$style.stage, $style[`_${stageStatus(item.id)}`]]"
            >
              <span :class="$style.stageDot" />
              <span :class="$style.stageLabel">{{ item.label }}</span>
            </li>
          </ol>

          <div ref="logRef" :class="$style.log">
            <div
              v-for="line in logs"
              :key="line.id"
              :class="[
                $style.logLine,
                line.stage === 'warn' && $style._warn,
                line.stage === 'error' && $style._error,
                line.stage === 'done' && $style._done,
              ]"
            >
              <span :class="$style.logTime">
                {{ new Date(line.at).toLocaleTimeString('ru-RU') }}
              </span>
              <span :class="$style.logMsg">
                <template v-if="line.company">
                  <span :class="$style.logCompany">{{ line.company }}</span>
                  ·
                </template>
                {{ line.message }}
              </span>
            </div>
            <p v-if="!logs.length" :class="$style.logEmpty">Жду первые сообщения о ходе загрузки…</p>
          </div>
        </section>
      </div>
    </div>
  </Transition>
</template>

<style module lang="scss">
.shell {
  display: grid;
  grid-template-rows: 1fr;
}

.shellInner {
  overflow: hidden;
  min-height: 0;
}

.LiveProgressPanel {
  display: grid;
  gap: var(--space-3);
  margin: var(--space-4) 0 0;
  padding: 0 0 var(--space-4);
  background: var(--color-panel);
  border-radius: var(--radius-xl);
  overflow: hidden;
}

.header {
  display: grid;
  grid-template-columns: auto 1fr auto;
  gap: var(--space-3);
  align-items: center;
  padding: 0 var(--space-5);
}

.pulseWrap {
  position: relative;
  width: 1.75rem;
  height: 1.75rem;
}

.pulseCore {
  position: absolute;
  inset: 0.45rem;
  border-radius: 50%;
  background: var(--color-accent);
}

.pulseRing {
  position: absolute;
  inset: 0;
  border: 0.125rem solid var(--color-accent);
  border-radius: 50%;
  opacity: 0.45;
  animation: pulseRing 1.4s var(--ease) infinite;
}

.copy {
  min-width: 0;
}

.title {
  margin: 0;
  @include text(h2);
}

.message {
  margin: 0.2rem 0 0;
  @include text(caption);
  color: var(--color-muted);
  min-height: 1.2em;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.counter {
  @include text(mono);
  font-size: 1rem;
  font-weight: 600;
  color: var(--color-ink);
  font-variant-numeric: tabular-nums;
}

.headerAside {
  display: flex;
  align-items: center;
  gap: 0.75rem;
}

.cancelBtn {
  appearance: none;
  border: 0;
  border-radius: var(--radius);
  background: var(--color-raised);
  color: var(--color-muted);
  padding: 0.4rem 0.75rem;
  @include text(caption);
  font-weight: 600;
  cursor: pointer;
  transition:
    color var(--dur) var(--ease),
    background-color var(--dur) var(--ease);

  @include hover {
    color: var(--color-danger);
    background: var(--color-danger-soft);
  }
}

.counterValue {
  color: var(--color-accent);
}

.counterSep {
  margin: 0 0.15rem;
  color: var(--color-faint);
}

.barTrack {
  height: 0.2rem;
  background: var(--color-raised);
}

.barFill {
  height: 100%;
  background: var(--color-accent);
  transition: width 0.25s var(--ease);
}

.stages {
  display: flex;
  flex-wrap: wrap;
  gap: 0.35rem;
  margin: 0;
  padding: 0 var(--space-5);
  list-style: none;
}

.stage {
  display: inline-flex;
  align-items: center;
  gap: 0.4rem;
  padding: 0.35rem 0.7rem;
  border-radius: var(--radius);
  background: var(--color-raised);
  color: var(--color-faint);
  transition:
    color var(--dur) var(--ease),
    background-color var(--dur) var(--ease);

  &._active {
    color: var(--color-accent-text);
    background: var(--color-accent);

    .stageDot {
      background: var(--color-accent-text);
      animation: dotBlink 1s ease infinite;
    }
  }

  &._done {
    color: var(--color-muted);

    .stageDot {
      background: var(--color-success);
    }
  }
}

.stageDot {
  width: 0.35rem;
  height: 0.35rem;
  border-radius: 50%;
  background: var(--color-faint);
}

.stageLabel {
  @include text(caption);
  font-weight: 600;
}

.log {
  max-height: 10rem;
  overflow: auto;
  margin: 0 var(--space-4);
  padding: var(--space-3);
  border-radius: var(--radius);
  background: var(--color-void);
  scroll-behavior: smooth;
}

.logLine {
  display: grid;
  grid-template-columns: 5.25rem 1fr;
  gap: var(--space-3);
  padding: 0.3rem 0;
  border-bottom: 0.0625rem solid color-mix(in srgb, var(--color-line) 60%, transparent);
  animation: lineIn 0.25s var(--ease) both;

  &:last-child {
    border-bottom: 0;
  }

  &._warn .logMsg {
    color: var(--color-warning);
  }

  &._error .logMsg {
    color: var(--color-danger);
  }

  &._done .logMsg {
    color: var(--color-success);
  }
}

.logTime {
  @include text(mono);
  color: var(--color-faint);
}

.logMsg {
  @include text(mono);
  color: var(--color-muted);
  word-break: break-word;
}

.logCompany {
  color: var(--color-ink);
  font-weight: 600;
}

.logEmpty {
  margin: 0;
  @include text(caption);
  color: var(--color-faint);
}

@keyframes pulseRing {
  0% {
    transform: scale(0.7);
    opacity: 0.7;
  }

  100% {
    transform: scale(1.25);
    opacity: 0;
  }
}

@keyframes dotBlink {
  0%,
  100% {
    opacity: 1;
  }

  50% {
    opacity: 0.45;
  }
}

@keyframes lineIn {
  from {
    opacity: 0;
    transform: translateY(0.25rem);
  }

  to {
    opacity: 1;
    transform: none;
  }
}
</style>

<style lang="scss">
.progress-expand-enter-active,
.progress-expand-leave-active {
  transition:
    grid-template-rows 0.38s var(--ease, cubic-bezier(0.12, 1, 0.48, 1)),
    opacity 0.28s var(--ease, cubic-bezier(0.12, 1, 0.48, 1));
  display: grid;
  overflow: hidden;
}

.progress-expand-enter-from,
.progress-expand-leave-to {
  grid-template-rows: 0fr;
  opacity: 0;
}

.progress-expand-enter-to,
.progress-expand-leave-from {
  grid-template-rows: 1fr;
  opacity: 1;
}
</style>
