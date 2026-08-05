/** Плавная прокрутка окна: к верху, к низу или к элементу. */

function preferBehavior(behavior?: ScrollBehavior): ScrollBehavior {
  if (behavior) {
    return behavior
  }
  if (typeof window !== 'undefined' && window.matchMedia('(prefers-reduced-motion: reduce)').matches) {
    return 'instant'
  }
  return 'smooth'
}

/**
 * Прокручивает окно к верху страницы.
 */
export function scrollToTop(behavior?: ScrollBehavior): void {
  window.scrollTo({ top: 0, left: 0, behavior: preferBehavior(behavior) })
}

/**
 * Прокручивает окно в самый низ страницы (футер у нижнего края экрана).
 */
export function scrollToBottom(behavior?: ScrollBehavior): void {
  const top = Math.max(
    document.documentElement.scrollHeight,
    document.body.scrollHeight,
  )
  window.scrollTo({ top, left: 0, behavior: preferBehavior(behavior) })
}

/**
 * Плавно прокручивает к элементу по CSS-селектору.
 * @param selector — CSS-селектор целевого элемента
 * @param offset — отступ сверху (px), чтобы не прилипать к краю
 */
export function scrollToSelector(
  selector: string,
  offset = 0,
  behavior?: ScrollBehavior,
): void {
  const element = document.querySelector(selector)
  if (!element) {
    return
  }
  const top = element.getBoundingClientRect().top + window.pageYOffset - offset
  window.scrollTo({ top: Math.max(0, top), left: 0, behavior: preferBehavior(behavior) })
}

/**
 * Ждёт отрисовки (два кадра) — удобно после появления Transition/v-if.
 */
export function afterPaint(): Promise<void> {
  return new Promise((resolve) => {
    requestAnimationFrame(() => {
      requestAnimationFrame(() => resolve())
    })
  })
}
