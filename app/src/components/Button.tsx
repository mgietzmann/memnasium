// Two kinds only: primary, disabled until its form is complete, and danger, which always
// confirms — design/app/Components.md.

import type { ReactNode } from 'react';

export interface ButtonProps {
  children: ReactNode;
  kind?: 'primary' | 'danger';
  disabled?: boolean;
  onClick?: () => void;
}

export function Button({ children, kind = 'primary', disabled = false, onClick }: ButtonProps) {
  return (
    <button type="button" className={`button button-${kind}`} disabled={disabled} onClick={onClick}>
      {children}
    </button>
  );
}
