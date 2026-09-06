import '@testing-library/jest-dom/vitest';

// jsdom has no `matchMedia`, and the theme asks it what the OS prefers when the
// toggle has never been used — design/standards/Style.md#choosing-a-theme.
if (!window.matchMedia) {
  window.matchMedia = ((query: string) => ({
    matches: false,
    media: query,
    onchange: null,
    addListener: () => {},
    removeListener: () => {},
    addEventListener: () => {},
    removeEventListener: () => {},
    dispatchEvent: () => false,
  })) as typeof window.matchMedia;
}
