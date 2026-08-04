<script setup lang="ts">
/**
 * Футер: контакты и дата.
 */
const AUTHOR_NAME = 'Кирилл Корнеев'
const AUTHOR_EMAIL = 'krllkrnv@yandex.ru'
const AUTHOR_TELEGRAM = 'kkorneev02'
const AUTHOR_GITHUB = 'krllkrnv'

const now = new Date()
const todayLabel = new Intl.DateTimeFormat('ru-RU', {
  day: 'numeric',
  month: 'long',
  year: 'numeric',
}).format(now)
const todayIso = now.toISOString().slice(0, 10)
</script>

<template>
  <footer :class="$style.TheFooter">
    <div :class="$style.author">
      <span :class="$style.name">{{ AUTHOR_NAME }}</span>
      <span :class="$style.sep" aria-hidden="true">·</span>
      <a :class="$style.link" :href="`mailto:${AUTHOR_EMAIL}`">
        {{ AUTHOR_EMAIL }}
      </a>
    </div>
    <div :class="$style.links">
      <a
        :class="$style.link"
        :href="`https://t.me/${AUTHOR_TELEGRAM}`"
        target="_blank"
        rel="noreferrer"
      >
        Telegram
      </a>
      <span :class="$style.sep" aria-hidden="true">·</span>
      <a
        :class="$style.link"
        :href="`https://github.com/${AUTHOR_GITHUB}`"
        target="_blank"
        rel="noreferrer"
      >
        GitHub
      </a>
      <span :class="$style.sep" aria-hidden="true">·</span>
      <time :class="$style.date" :datetime="todayIso">{{ todayLabel }}</time>
    </div>
  </footer>
</template>

<style module lang="scss">
.TheFooter {
  margin-top: auto;
  padding: var(--space-6) 0 var(--space-4);
  display: flex;
  flex-wrap: wrap;
  justify-content: space-between;
  gap: var(--space-3);
  border-top: 0.0625rem solid var(--color-line);
}

.author,
.links {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 0.35rem 0.5rem;
}

.name {
  @include text(caption);
  font-weight: 600;
  color: var(--color-ink);
}

.link {
  @include text(caption);
  color: var(--color-muted);
  text-decoration: none;

  &:hover {
    color: var(--color-ink);
  }
}

.sep {
  color: var(--color-line-strong);
}

.date {
  @include text(caption);
  color: var(--color-faint);
}
</style>
