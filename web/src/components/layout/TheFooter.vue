<script setup lang="ts">
/**
 * Футер: контакты и дата.
 */
const AUTHOR_EMAIL = 'krllkrnv@yandex.ru'
const AUTHOR_TELEGRAM = 'kkorneev02'
const AUTHOR_GITHUB = 'krllkrnv'

const now = new Date()
const yearLabel = String(now.getFullYear())
const yearIso = yearLabel
</script>

<template>
  <footer id="hh-footer" :class="$style.TheFooter">
    <div :class="$style.contacts">
      <a :class="$style.link" :href="`mailto:${AUTHOR_EMAIL}`">
        {{ AUTHOR_EMAIL }}
      </a>
      <span :class="$style.sep" aria-hidden="true">·</span>
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
    </div>
    <time :class="$style.date" :datetime="yearIso">{{ yearLabel }}</time>
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
}

.contacts {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 0.35rem 0.5rem;
}

.link {
  @include text(caption);
  color: var(--color-faint);
  text-decoration: none;

  @include hover {
    color: var(--color-accent);
  }
}

.sep {
  color: var(--color-line);
}

.date {
  @include text(caption);
  color: var(--color-faint);
}
</style>
