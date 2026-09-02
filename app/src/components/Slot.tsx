// A blank holding one reference: empty, filled, or locked.
// The three states are drawn by border and fill before any colour is applied, so turning every
// colour off still tells them apart — design/standards/Style.md.

import type { ReactNode } from 'react';

export type SlotState = 'empty' | 'filled' | 'locked';

export interface SlotProps {
  /** What the slot holds — `clade` or `source`. Becomes its accessible name. */
  kind: 'clade' | 'source';
  state: SlotState;
  value?: ReactNode;
  onClick?: () => void;
}

export function Slot({ kind, state, value, onClick }: SlotProps) {
  const locked = state === 'locked';
  return (
    <button
      type="button"
      className={`slot slot-${state}`}
      aria-label={`${kind} slot`}
      aria-disabled={locked}
      disabled={locked}
      onClick={locked ? undefined : onClick}
    >
      <span className="slot-value">{state === 'empty' ? ' ' : value}</span>
      {locked && (
        <span className="slot-check" aria-hidden="true">
          ✓
        </span>
      )}
    </button>
  );
}
