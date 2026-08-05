<script setup lang="ts">
/**
 * Экран входа: загрузка чатов по cookie или открытие уже готового отчёта из файла.
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
 * Отправляет cookie и период на сервер для синхронизации с hh.
 * Текст cookie в поле оставляем: если синхронизация упадёт с ошибкой,
 * можно нажать кнопку ещё раз без повторной вставки. Когда отчёт
 * успешно загрузится, этот экран просто скроется вместе с полем.
 */
function handleSync(): void {
  const clamped = Math.min(180, Math.max(1, Number(days.value) || DEFAULT_SYNC_DAYS))
  days.value = String(clamped)
  emit('sync', {
    cookie: cookie.value.trim(),
    days: clamped,
    hhHost: hhHost.value.trim(),
  })
}

/**
 * Берёт выбранный файл отчёта и отдаёт его родителю на разбор.
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
 * Открывает системное окно выбора файла.
 */
function handlePickFile(): void {
  fileInput.value?.click()
}
</script>

<template>
  <section :class="$style.SetupPanel">
    <header :class="$style.masthead">
      <BrandTitle />
      <p :class="$style.lead">
        Разбирает переписки с работодателями на hh.ru: приглашения, тестовые и то, где ещё
        ожидается ваш ответ. Чаты подтягиваются по cookie из браузера. Если отчёт уже скачан из
        дашборда раньше, cookie не нужен — откройте файл справа.
      </p>
      <div :class="$style.accentLine" aria-hidden="true" />
    </header>

    <div :class="$style.workspace">
      <form :class="$style.syncForm" @submit.prevent="handleSync">
        <div :class="$style.sectionHead">
          <h2 :class="$style.sectionTitle">Загрузить чаты с hh</h2>
          <ol :class="$style.steps">
            <li>
              Открой
              <a href="https://hh.ru" target="_blank" rel="noreferrer">hh.ru</a>
              и войди в аккаунт.
            </li>
            <li>
              Нажми
              <span :class="$style.code">F12</span>
              — откроются инструменты разработчика.
            </li>
            <li>
              Открой вкладку
              <span :class="$style.code">Network</span>
              (Сеть) и нажми
              <span :class="$style.code">Ctrl+R</span>, чтобы страница перезагрузилась и в списке
              появились запросы.
            </li>
            <li>Кликни любой запрос к hh.ru в списке.</li>
            <li>
              В блоке заголовков запроса найди строку
              <span :class="$style.code">Cookie</span>
              и скопируй её значение целиком.
            </li>
            <li>
              Вставь сюда. Формат не важен: строка Cookie, JSON «Request Cookies» из DevTools или
              таблица из Application → Cookies — разберём сами. Нужны
              <span :class="$style.code">hhtoken</span>
              и
              <span :class="$style.code">_xsrf</span>.
            </li>
          </ol>
        </div>

        <label :class="$style.field">
          <span :class="$style.fieldLabel">Cookie из браузера</span>
          <textarea
            v-model="cookie"
            :class="$style.textarea"
            rows="5"
            placeholder="Cookie-строка или JSON Request Cookies — например: hhtoken=…; _xsrf=…"
            required
            autocomplete="off"
            spellcheck="false"
          />
        </label>

        <div :class="$style.row">
          <label :class="$style.field">
            <span :class="$style.fieldLabel">За сколько дней</span>
            <UiTextInput v-model="days" type="number" min="1" max="180" />
          </label>
          <label :class="$style.field">
            <span :class="$style.fieldLabel">Сайт hh</span>
            <UiTextInput v-model="hhHost" placeholder="https://hh.ru" />
          </label>
        </div>
        <p :class="$style.hint">
          Берутся чаты, в которых что-то происходило за выбранный срок (последнее сообщение или
          активность). Дата отклика на вакансию тут не учитывается. Можно указать от 1 до 180 дней.
        </p>

        <div :class="$style.actions">
          <UiButton
            type="submit"
            :disabled="props.loading || !cookie.trim()"
            :loading="props.loading"
          >
            Загрузить чаты
          </UiButton>
          <UiButton
            v-if="canCancelSetup"
            type="button"
            :variant="EButtonVariant.Ghost"
            :disabled="props.loading"
            @click="emit('cancelSetup')"
          >
            Вернуться к отчёту
          </UiButton>
        </div>
      </form>

      <aside :class="$style.uploadPane">
        <p :class="$style.kicker">Без cookie</p>
        <h2 :class="$style.sectionTitle">Открыть готовый отчёт</h2>
        <p :class="$style.hint">
          Файл, который вы скачали из этого дашборда: JSON или Excel. Cookie для этого не нужен.
        </p>

        <input
          id="hh-leads-upload"
          ref="fileInput"
          type="file"
          accept=".xlsx,.json,application/json,application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
          hidden
          @change="handleFileChange"
        />

        <div
          :class="$style.uploadDrop"
          role="button"
          tabindex="0"
          aria-controls="hh-leads-upload"
          aria-label="Выбрать скачанный отчёт JSON или Excel"
          @click="handlePickFile"
          @keydown.enter.prevent="handlePickFile"
          @keydown.space.prevent="handlePickFile"
        >
          <UiButton
            :variant="EButtonVariant.Ghost"
            :disabled="props.loading"
            @click.stop="handlePickFile"
          >
            Выбрать файл
          </UiButton>
          <p :class="$style.uploadHint">JSON или Excel (.xlsx)</p>
        </div>
        <p v-if="fileName" :class="$style.fileName">Выбран файл: {{ fileName }}</p>
      </aside>
    </div>
  </section>
</template>

<style module lang="scss">
.SetupPanel {
  @include fade-up;
  display: grid;
  gap: var(--space-7);
  padding: var(--space-4) 0 var(--space-4);
  align-content: start;
}

.masthead {
  display: grid;
  gap: var(--space-4);
  max-width: 38rem;
}

.lead {
  margin: 0;
  @include text(body-lg);
  color: var(--color-muted);
}

.accentLine {
  width: 3.25rem;
  height: 0.125rem;
  background: var(--color-hh);
  transform-origin: left center;
  animation: revealLine 0.45s var(--ease) both;
}

.workspace {
  display: grid;
  gap: var(--space-4);
  align-items: stretch;

  @include respond-to(from-desktop) {
    grid-template-columns: minmax(0, 1.6fr) minmax(0, 0.85fr);
  }
}

.syncForm,
.uploadPane {
  display: grid;
  gap: var(--space-4);
  padding: var(--space-6);
  background: var(--color-panel);
  border-radius: var(--radius-xl);
  align-content: start;
}

.sectionHead {
  display: grid;
  gap: var(--space-2);
}

.kicker {
  margin: 0;
  @include text(label);
  color: var(--color-faint);
}

.sectionTitle {
  margin: 0;
  @include text(h2);
  color: var(--color-ink);
}

.hint {
  margin: 0;
  @include text(dense);
  color: var(--color-muted);
  max-width: 36rem;
}

.steps {
  margin: 0;
  padding: 0 0 0 1.15rem;
  display: grid;
  gap: 0.35rem;
  @include text(dense);
  color: var(--color-muted);
  max-width: 36rem;

  li {
    padding-left: 0.15rem;
  }

  a {
    color: var(--color-accent);
    text-decoration: none;

    @include hover {
      color: var(--color-accent-hover);
      text-decoration: underline;
    }
  }
}

.code {
  color: var(--color-accent);
  font-weight: 600;
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
  padding: 1rem;
  border: 0.0625rem solid transparent;
  border-radius: var(--radius);
  background: var(--color-raised);
  color: var(--color-ink);
  resize: vertical;
  font-size: 0.875rem;
  font-weight: 500;
  line-height: 1.45;
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
}

.row {
  display: grid;
  gap: var(--space-3);

  @include respond-to(from-tablet) {
    grid-template-columns: 10.5rem 1fr;
  }
}

.actions {
  display: flex;
  flex-wrap: wrap;
  gap: var(--space-2);
  padding-top: var(--space-2);
}

.uploadDrop {
  display: grid;
  gap: var(--space-3);
  justify-items: start;
  padding: var(--space-5);
  border-radius: var(--radius-lg);
  background: var(--color-raised);
  cursor: pointer;
  transition: background-color var(--dur) var(--ease);

  @include hover {
    background: color-mix(in srgb, var(--color-accent-soft) 55%, var(--color-raised));
  }
}

.uploadHint {
  margin: 0;
  @include text(mono);
  color: var(--color-faint);
}

.fileName {
  margin: 0;
  @include text(caption);
  color: var(--color-muted);
  word-break: break-all;
}
</style>
