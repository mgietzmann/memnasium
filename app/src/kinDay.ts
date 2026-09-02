// The table in design/app/Navigation.md, in one place: a set outlives the day it was drawn on,
// so the date it was drawn is what separates *finished today* from *never started* — and an open
// board outranks every other row of it.

import type { KinState } from './api/types';

/**
 * The player's local date.
 *
 * The server stamps `generated_on` with its own `date.today()`, which is local time, so the
 * client has to agree. `toISOString()` would be UTC: west of Greenwich the client would believe
 * it was already tomorrow every evening, read `not generated` over a set drawn hours earlier,
 * and offer a Generate that does nothing. `en-CA` is the locale that formats as `YYYY-MM-DD`.
 */
function today(): string {
  return new Date().toLocaleDateString('en-CA');
}

/** What the games card shows. Progress is counted in anchors resolved, never in edges. */
export function kinStateLine(state: KinState | null): string {
  if (!state || state.generated_on === null) return 'not generated';
  // An open board outranks everything else: every anchor can be dealt and the last board still
  // be half-played, and the card must not invite a draw that would throw it away.
  if (state.open_board) return 'board in progress';
  if (state.anchors_left === 0) {
    return state.generated_on === today() ? 'done for today' : 'not generated';
  }
  return `${state.anchors_total - state.anchors_left} / ${state.anchors_total} anchors`;
}

/**
 * Whether the day's draw still has to be made.
 *
 * A set left unfinished carries over instead, and a set with an open board is never spent — so
 * Generate is never offered while a board is open (design/app/Kin.md).
 */
export function needsGenerate(state: KinState | null): boolean {
  if (!state || state.generated_on === null) return true;
  if (state.open_board) return false;
  return state.anchors_left === 0 && state.generated_on !== today();
}
