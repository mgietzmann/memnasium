// A short tappable label — the clade palette, the citation pool, and every search result.
// A chip is never consumed: selecting one does not remove it (design/app/Components.md).

import type { ReactNode } from 'react';

export interface ChipProps {
  children: ReactNode;
  selected?: boolean;
  onClick?: () => void;
}

export function Chip({ children, selected = false, onClick }: ChipProps) {
  return (
    <button
      type="button"
      className={selected ? 'chip chip-selected' : 'chip'}
      aria-pressed={selected}
      onClick={onClick}
    >
      {children}
    </button>
  );
}
