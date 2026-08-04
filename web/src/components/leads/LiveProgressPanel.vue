<script setup lang="ts">
/**
 * Живая панель прогресса синка/upload: этапы, бар, лог.
 */
import { computed, nextTick, ref, watch } from 'vue'
import type { ProgressStage } from '@/types/progress'
import { PROGRESS_STAGES } from '@/types/progress'

type LogItem = {
  id: number
  stage: ProgressStage | 'info'
  message: string
  company?: string
  at: number
}

const props = defineProps<{
  active: boolean
  mode: 'sync' | 'upload' | 'boot' | null
  stage: ProgressStage | null
  message: string
  current: number
  total: number
  percent: number
  logs: LogItem[]
}>()

const logRef = ref<HTMLElement | null>(null)

const title = computed(() => {
  if (props.mode === 'upload') {
    return 'Загрузка файла'
  }
  if (props.mode === 'boot') {
    return 'Проверка сессии'
  }
  return 'Синхронизация чатов'
})

const visibleStages = computed(() => {
  if (props.mode === 'upload') {
    return PROGRESS_STAGES.filter((item) =>
      ['parse', 'classify', 'build'].includes(item.id),
    )
  }
  return PROGRESS_STAGES.filter((item) =>
    ['auth', 'list', 'fetch', 'classify', 'build'].includes(item.id),
  )
})

const stageOrder = computed(() => visibleStages.value.map((item) => item.id))

/**
 * Статус этапа для индикатора: pending / active / done.
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
  <Transition name="live-fade">
    <section
      v-if="active"
      :class="$style.LiveProgressPanel"
      role="status"
      aria-live="polite"
      aria-busy="true"
    >
      <div :class="$style.glow" aria-hidden="true" />

      <header :class="$style.header">
        <div :class="$style.pulseWrap" aria-hidden="true">
          <span :class="$style.pulseCore" />
          <span :class="$style.pulseRing" />
        </div>
        <div>
          <h2 :class="$style.title">{{ title }}</h2>
          <p :class="$style.message">{{ message || 'Работаю…' }}</p>
        </div>
        <div v-if="total > 0" :class="$style.counter">
          <span :class="$style.counterValue">{{ current }}</span>
          <span :class="$style.counterSep">/</span>
          <span>{{ total }}</span>
        </div>
      </header>

      <div :class="$style.barTrack" aria-hidden="true">
        <div
          :class="$style.barFill"
          :style="{ width: `${Math.max(percent, total ? 4 : 12)}%` }"
        />
        <div :class="$style.barSheen" />
      </div>

      <ol :class="$style.stages">
        <li
          v-for="item in visibleStages"
          :key="item.id"
          :class="[
            $style.stage,
            $style[`_${stageStatus(item.id)}`],
          ]"
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
        <p v-if="!logs.length" :class="$style.logEmpty">Жду первые события…</p>
      </div>
    </section>
  </Transition>
</template>

<style module lang="scss">
.LiveProgressPanel {
  @include fade-up;
  position: relative;
  overflow: hidden;
  display: grid;
  gap: var(--space-4);
  margin: var(--space-4) 0;
  padding: var(--space-5);
  border: 0.0625rem solid var(--color-line);
  border-radius: var(--radius-lg);
  background: var(--color-panel);
}

.glow {
  pointer-events: none;
  position: absolute;
  inset: -40% auto auto -20%;
  width: 18rem;
  height: 18rem;
  background: radial-gradient(circle, rgb(59 130 246 / 18%), transparent 70%);
  animation: glowDrift 6s var(--ease) infinite alternate;
}

.header {
  position: relative;
  display: grid;
  grid-template-columns: auto 1fr auto;
  gap: var(--space-4);
  align-items: center;
}

.pulseWrap {
  position: relative;
  width: 2.25rem;
  height: 2.25rem;
}

.pulseCore {
  position: absolute;
  inset: 0.55rem;
  border-radius: 50%;
  background: var(--color-accent);
  box-shadow: 0 0 0.75rem rgb(59 130 246 / 45%);
}

.pulseRing {
  position: absolute;
  inset: 0;
  border: 0.125rem solid var(--color-accent);
  border-radius: 50%;
  opacity: 0.55;
  animation: pulseRing 1.4s var(--ease) infinite;
}

.title {
  margin: 0;
  @include text(h2);
}

.message {
  margin: 0.35rem 0 0;
  @include text(caption);
  color: var(--color-muted);
  min-height: 1.2em;
}

.counter {
  @include text(mono-lg);
  font-size: 1.25rem;
  color: var(--color-ink);
  font-variant-numeric: tabular-nums;
}

.counterValue {
  color: var(--color-accent);
}

.counterSep {
  margin: 0 0.15rem;
  color: var(--color-faint);
}

.barTrack {
  position: relative;
  overflow: hidden;
  height: 0.375rem;
  border-radius: 999px;
  background: var(--color-raised);
}

.barFill {
  height: 100%;
  border-radius: inherit;
  background: linear-gradient(
    90deg,
    var(--color-accent),
    var(--color-accent-hover)
  );
  transition: width 0.25s var(--ease);
}

.barSheen {
  position: absolute;
  inset: 0;
  background: linear-gradient(
    110deg,
    transparent 30%,
    rgb(255 255 255 / 18%) 50%,
    transparent 70%
  );
  background-size: 200% 100%;
  animation: sheen 1.6s linear infinite;
}

.stages {
  position: relative;
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(7rem, 1fr));
  gap: var(--space-2);
  margin: 0;
  padding: 0;
  list-style: none;
}

.stage {
  display: grid;
  gap: 0.4rem;
  justify-items: start;
  padding: 0.55rem 0.65rem;
  border: 0.0625rem solid var(--color-line);
  border-radius: var(--radius);
  background: var(--color-raised);
  color: var(--color-faint);
  transition:
    border-color var(--dur) var(--ease),
    color var(--dur) var(--ease),
    background-color var(--dur) var(--ease);

  &._active {
    border-color: var(--color-accent);
    color: var(--color-ink);
    background: var(--color-accent-soft);

    .stageDot {
      background: var(--color-accent);
      box-shadow: 0 0 0 0.25rem rgb(59 130 246 / 20%);
      animation: dotBlink 1s ease infinite;
    }
  }

  &._done {
    color: var(--color-success);
    border-color: color-mix(in srgb, var(--color-success) 45%, var(--color-line));

    .stageDot {
      background: var(--color-success);
    }
  }
}

.stageDot {
  width: 0.45rem;
  height: 0.45rem;
  border-radius: 50%;
  background: var(--color-faint);
}

.stageLabel {
  @include text(caption);
  font-weight: 600;
}

.log {
  position: relative;
  max-height: 14rem;
  overflow: auto;
  padding: var(--space-3);
  border: 0.0625rem solid var(--color-line);
  border-radius: var(--radius);
  background: var(--color-void);
  scroll-behavior: smooth;
}

.logLine {
  display: grid;
  grid-template-columns: 5.5rem 1fr;
  gap: var(--space-3);
  padding: 0.35rem 0;
  border-bottom: 0.0625rem solid color-mix(in srgb, var(--color-line) 70%, transparent);
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

@keyframes sheen {
  from {
    background-position: 200% 0;
  }

  to {
    background-position: -200% 0;
  }
}

@keyframes glowDrift {
  from {
    transform: translate(0, 0);
  }

  to {
    transform: translate(2rem, 1rem);
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
.live-fade-enter-active,
.live-fade-leave-active {
  transition:
    opacity 0.25s ease,
    transform 0.25s ease;
}

.live-fade-enter-from,
.live-fade-leave-to {
  opacity: 0;
  transform: translateY(0.4rem);
}
</style>
