/**
 * The calendar, used in exactly one place: deciding whether Build is offered.
 *
 * Nothing else in the app compares dates — the current draw is whatever was
 * most recently built, and it stays current until the next one replaces it.
 * See design/Data.md#the-draw.
 */
export function todayIso(): string {
  const now = new Date();
  const pad = (n: number) => String(n).padStart(2, '0');
  return `${now.getFullYear()}-${pad(now.getMonth() + 1)}-${pad(now.getDate())}`;
}

/** A draw's date, as the screens print it: `3 Sep`. */
export function shortDay(iso: string): string {
  const [y, m, d] = iso.split('-').map(Number);
  const months = [
    'Jan',
    'Feb',
    'Mar',
    'Apr',
    'May',
    'Jun',
    'Jul',
    'Aug',
    'Sep',
    'Oct',
    'Nov',
    'Dec',
  ];
  return `${d} ${months[m - 1] ?? ''} ${y === new Date().getFullYear() ? '' : y}`.trim();
}

/** Whether the current draw still has anything in it. */
export function anythingLeft(draw: { due: number }): boolean {
  return draw.due > 0;
}
