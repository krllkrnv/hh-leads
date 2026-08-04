<script setup lang="ts">
import { ref } from 'vue'
import UiButton from '@/components/ui/UiButton.vue'
import UiTextInput from '@/components/ui/UiTextInput.vue'

const props = defineProps<{
  loading?: boolean
}>()

const emit = defineEmits<{
  sync: [payload: { cookie: string; days: number; hhHost: string }]
  upload: [file: File]
}>()

const cookie = ref('')
const days = ref('60')
const hhHost = ref('')
const fileInput = ref<HTMLInputElement | null>(null)

function onSync() {
  const daysNum = Number(days.value) || 60
  emit('sync', {
    cookie: cookie.value.trim(),
    days: daysNum,
    hhHost: hhHost.value.trim(),
  })
}

function onFileChange(event: Event) {
  const input = event.target as HTMLInputElement
  const file = input.files?.[0]
  if (file) emit('upload', file)
  input.value = ''
}
</script>

<template>
  <section :class="$style.setupPanel">
    <header :class="$style.header">
      <h1 :class="$style.title">HH Leads</h1>
      <p :class="$style.lead">
        Локальный дашборд лидов из чатов hh.ru. Данные ваши: cookie для синка
        или загрузка Excel/JSON из CLI.
      </p>
    </header>

    <div :class="$style.grid">
      <form :class="$style.block" @submit.prevent="onSync">
        <h2 :class="$style.blockTitle">Синхронизация по cookie</h2>
        <p :class="$style.hint">
          F12 → Network → любой запрос к hh.ru → скопируйте заголовок Cookie.
          Нужны hhtoken и _xsrf. Cookie остаётся в памяти сессии сервера, на
          диск не пишется.
        </p>
        <label :class="$style.label">
          Cookie
          <textarea
            v-model="cookie"
            :class="$style.textarea"
            rows="4"
            placeholder="hhtoken=…; _xsrf=…; …"
            required
          />
        </label>
        <div :class="$style.row">
          <label :class="$style.label">
            Дней
            <UiTextInput v-model="days" type="number" />
          </label>
          <label :class="$style.label">
            Host (опционально)
            <UiTextInput v-model="hhHost" placeholder="https://hh.ru" />
          </label>
        </div>
        <UiButton type="submit" :disabled="props.loading || !cookie.trim()">
          Загрузить чаты
        </UiButton>
      </form>

      <div :class="$style.block">
        <h2 :class="$style.blockTitle">Загрузка файла</h2>
        <p :class="$style.hint">
          Подойдёт xlsx из `python analyze_chats.py` или json-отчёт дашборда.
        </p>
        <input
          ref="fileInput"
          type="file"
          accept=".xlsx,.json,application/json,application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
          hidden
          @change="onFileChange"
        />
        <UiButton
          variant="ghost"
          :disabled="props.loading"
          @click="fileInput?.click()"
        >
          Выбрать файл
        </UiButton>
      </div>
    </div>
  </section>
</template>

<style module lang="scss">
.setupPanel {
  display: grid;
  gap: 1.5rem;
}

.header {
  max-width: 42rem;
}

.title {
  margin: 0;
  font-family: var(--font-display);
  font-size: 2.4rem;
  font-weight: 600;
  letter-spacing: -0.03em;
}

.lead {
  margin: 0.6rem 0 0;
  color: var(--color-muted);
  line-height: 1.5;
}

.grid {
  display: grid;
  gap: 1rem;

  @media (min-width: 56rem) {
    grid-template-columns: 1.4fr 1fr;
  }
}

.block {
  background: var(--color-surface);
  border: 0.0625rem solid var(--color-border);
  border-radius: 0.75rem;
  padding: 1.1rem;
  display: grid;
  gap: 0.85rem;
  align-content: start;
}

.blockTitle {
  margin: 0;
  font-size: 1.05rem;
}

.hint {
  margin: 0;
  color: var(--color-muted);
  font-size: 0.9rem;
  line-height: 1.45;
}

.label {
  display: grid;
  gap: 0.35rem;
  font-size: 0.85rem;
  color: var(--color-muted);
}

.textarea {
  width: 100%;
  border: 0.0625rem solid var(--color-border);
  border-radius: 0.5rem;
  padding: 0.65rem 0.8rem;
  resize: vertical;
  font-family: ui-monospace, SFMono-Regular, Menlo, monospace;
  font-size: 0.8rem;
}

.row {
  display: grid;
  gap: 0.75rem;

  @media (min-width: 40rem) {
    grid-template-columns: 7rem 1fr;
  }
}
</style>
