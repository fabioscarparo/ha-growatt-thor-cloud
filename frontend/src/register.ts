/**
 * Resolves once Home Assistant's app has started (or, as a safety net, after 30 s).
 *
 * In browsers without scoped custom element registries, the app replaces
 * `window.customElements` with a polyfilled registry as it starts, and that
 * registry only knows the elements defined through it. This module is small and
 * can load before the app: an element defined at that point would stay unknown
 * to Home Assistant ("Custom element doesn't exist"). The app defines
 * `home-assistant` (or `hc-main` when casting) through the new registry.
 */
const appStarted = Promise.race([
  customElements.whenDefined("home-assistant"),
  customElements.whenDefined("hc-main"),
  new Promise((resolve) => setTimeout(resolve, 30_000)),
]);

/** Define a custom element in the registry Home Assistant uses. */
export function defineElement(tag: string, element: CustomElementConstructor): void {
  appStarted.then(() => {
    // Looked up now, not at load: by then the app may have replaced the registry.
    if (!customElements.get(tag)) {
      customElements.define(tag, element);
    }
  });
}
