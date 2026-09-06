/**
 * Which ground the app is read on — design/standards/Style.md#choosing-a-theme.
 *
 * The palettes are entirely in CSS; all this does is set (or clear) the
 * `data-theme` attribute the stylesheet keys off, and remember the choice per
 * browser. It is not in the database: nothing about which ground a board is read
 * on belongs in the study record.
 */

export type Ground = 'dark' | 'light';

const KEY = 'memnasium.theme';

/** The stored choice, or `null` while the toggle has never been used. */
export function stored(): Ground | null {
  const value = localStorage.getItem(KEY);
  return value === 'dark' || value === 'light' ? value : null;
}

/**
 * The ground actually on screen. There is no third "system" position: an
 * untouched install follows the OS, falling back to dark when it says nothing.
 */
export function ground(): Ground {
  return stored() ?? (matchMedia('(prefers-color-scheme: light)').matches ? 'light' : 'dark');
}

/** Store a choice and put it on the root, where the stylesheet reads it. */
export function choose(next: Ground): void {
  localStorage.setItem(KEY, next);
  document.documentElement.setAttribute('data-theme', next);
}

/** Reapply the stored choice on load. Without one the OS query decides. */
export function apply(): void {
  const choice = stored();
  if (choice) document.documentElement.setAttribute('data-theme', choice);
  else document.documentElement.removeAttribute('data-theme');
}
