<script setup lang="ts">
/**
 * Экран входа: cookie-sync или загрузка файла.
 */
import { ref } from 'vue'
import BrandTitle from '@/components/ui/BrandTitle.vue'
import UiButton from '@/components/ui/UiButton.vue'
import UiTextInput from '@/components/ui/UiTextInput.vue'
import { DEFAULT_SYNC_DAYS, EButtonVariant } from '@/types/report'

const props = defineProps<{
  loading?: boolean
  canCancelSetup?: boolean
}>()

const emit = defineEmits<{
  sync: [payload: { cookie: string; days: number; hhHost: string }]
  upload: [file: File]
  cancelSetup: []
}>()

const cookie = ref('')
const days = ref(String(DEFAULT_SYNC_DAYS))
const hhHost = ref('')
const fileInput = ref<HTMLInputElement | null>(null)
const fileName = ref('')

/**
 * Отправляет cookie и параметры периода на sync.
 */
function handleSync(): void {
  const clamped = Math.min(180, Math.max(1, Number(days.value) || DEFAULT_SYNC_DAYS))
  days.value = String(clamped)
  emit('sync', {
    cookie: cookie.value.trim(),
    days: clamped,
    hhHost: hhHost.value.trim(),
  })
  cookie.value = ''
}

/**
 * Читает выбранный файл и эмитит upload.
 */
function handleFileChange(event: Event): void {
  const input = event.target as HTMLInputElement
  const file = input.files?.[0]
  if (!file) {
    return
  }
  fileName.value = file.name
  emit('upload', file)
  input.value = ''
}

/**
 * Открывает системный file picker.
 */
function handlePickFile(): void {
  fileInput.value?.click()
}
</script>

<template>
  <section :class="$style.SetupPanel">
    <div :class="$style.masthead">
      <BrandTitle />
      <p :class="$style.lead">
        Анализ переписок с работодателями на hh.ru. Здесь собраны приглашения
        на собеседование, тестовые задания и активные обсуждения. Чаты
        забираются по cookie из браузера. Если отчёт уже есть в Excel, файл
        можно открыть без cookie.
      </p>
      <div :class="$style.accentLine" aria-hidden="true" />
    </div>

    <div :class="$style.workspace">
      <form :class="$style.syncForm" @submit.prevent="handleSync">
        <div :class="$style.sectionHead">
          <h2 :class="$style.sectionTitle">Синхронизация</h2>
          <p :class="$style.hint">
            После входа на hh.ru откройте инструменты разработчика в браузере,
            найдите любой запрос к сайту и скопируйте значение заголовка Cookie.
            В нём должны быть
            <span :class="$style.code">hhtoken</span>
            и
            <span :class="$style.code">_xsrf</span>.
            Cookie остаётся только в памяти текущей сессии и на диск не пишется.
          </p>
        </div>

        <label :class="$style.field">
          <span :class="$style.fieldLabel">Cookie</span>
          <textarea
            v-model="cookie"
            :class="$style.textarea"
            rows="6"
            placeholder="hhtoken=…; _xsrf=…; …"
            required
            autocomplete="off"
            spellcheck="false"
          />
        </label>

        <div :class="$style.row">
          <label :class="$style.field">
            <span :class="$style.fieldLabel">Дней</span>
            <UiTextInput v-model="days" type="number" min="1" max="180" />
          </label>
          <label :class="$style.field">
            <span :class="$style.fieldLabel">Host</span>
            <UiTextInput v-model="hhHost" placeholder="https://hh.ru" />
          </label>
        </div>

        <UiButton
          type="submit"
          :disabled="props.loading || !cookie.trim()"
          :loading="props.loading"
          full-width
        >
          Загрузить чаты
        </UiButton>

        <UiButton
          v-if="canCancelSetup"
          type="button"
          :variant="EButtonVariant.Ghost"
          :disabled="props.loading"
          full-width
          @click="emit('cancelSetup')"
        >
          Вернуться к отчёту
        </UiButton>
      </form>

      <aside :class="$style.uploadPane">
        <div :class="$style.sectionHead">
          <h2 :class="$style.sectionTitle">Файл</h2>
          <p :class="$style.hint">
            Подойдёт Excel с ранее сохранённым отчётом или JSON-файл отчёта.
            Cookie для этого способа не нужен.
          </p>
        </div>

        <input
          ref="fileInput"
          type="file"
          accept=".xlsx,.json,application/json,application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
          hidden
          @change="handleFileChange"
        />

        <UiButton
          :variant="EButtonVariant.Ghost"
          :disabled="props.loading"
          full-width
          @click="handlePickFile"
        >
          Выбрать xlsx / json
        </UiButton>
        <p v-if="fileName" :class="$style.fileName">{{ fileName }}</p>
      </aside>
    </div>
  </section>
</template>

<style module lang="scss">
.SetupPanel {
  @include fade-up;
  display: grid;
  gap: var(--space-7);
  padding: var(--space-6) 0 var(--space-5);
  align-content: start;
}

.masthead {
  display: grid;
  gap: var(--space-3);
  max-width: 36rem;
}

.lead {
  margin: 0;
  @include text(body-lg);
  color: var(--color-muted);
  max-width: 32rem;
}

.accentLine {
  width: 4.5rem;
  height: 0.1875rem;
  margin-top: var(--space-2);
  background: var(--color-hh);
  transform-origin: left center;
  animation: revealLine 0.5s var(--ease) both;
}

.workspace {
  display: grid;
  gap: var(--space-5);
  align-items: start;

  @include respond-to(from-desktop) {
    grid-template-columns: minmax(0, 1.4fr) minmax(0, 0.85fr);
    gap: var(--space-6);
  }
}

.syncForm,
.uploadPane {
  display: grid;
  gap: var(--space-4);
  padding: var(--space-5);
  background: var(--color-panel);
  border: 0.0625rem solid var(--color-line);
  border-radius: var(--radius-lg);
  border-left: 0.1875rem solid var(--color-accent);
}

.uploadPane {
  border-left-color: var(--color-line-strong);
  align-content: start;
  min-height: 100%;
}

.sectionHead {
  display: grid;
  gap: var(--space-2);
}

.sectionTitle {
  margin: 0;
  @include text(h2);
}

.hint {
  margin: 0;
  @include text(caption);
  color: var(--color-muted);
}

.code {
  @include text(mono);
  color: var(--color-accent);
}

.field {
  display: grid;
  gap: 0.4rem;
}

.fieldLabel {
  @include text(label);
  color: var(--color-faint);
}

.textarea {
  width: 100%;
  padding: 0.85rem;
  border: 0.0625rem solid var(--color-line);
  border-radius: var(--radius);
  background: var(--color-raised);
  color: var(--color-ink);
  resize: vertical;
  font-family: var(--font-mono);
  font-size: 0.8125rem;
  line-height: 1.5;
  transition: border-color var(--dur) var(--ease);

  &:hover {
    border-color: var(--color-line-strong);
  }

  &:focus {
    outline: none;
    border-color: var(--color-accent);
    box-shadow: var(--shadow-focus);
  }
}

.row {
  display: grid;
  gap: var(--space-3);

  @include respond-to(from-tablet) {
    grid-template-columns: 7rem 1fr;
  }
}

.fileName {
  margin: 0;
  @include text(mono);
  color: var(--color-muted);
  word-break: break-all;
}
</style>
