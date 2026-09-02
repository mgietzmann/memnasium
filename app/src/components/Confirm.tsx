// A modal asking once before something irreversible. One use today — Move on, which can fail a
// whole board in a tap (design/app/Components.md).

import { Button } from './Button';

export interface ConfirmProps {
  title: string;
  detail: string;
  confirmLabel: string;
  onConfirm: () => void;
  onCancel: () => void;
}

export function Confirm({ title, detail, confirmLabel, onConfirm, onCancel }: ConfirmProps) {
  return (
    <div className="modal-ground">
      <div className="modal" role="dialog" aria-modal="true" aria-label={title}>
        <h2>{title}</h2>
        <p className="common">{detail}</p>
        <div className="row">
          <Button kind="danger" onClick={onConfirm}>
            {confirmLabel}
          </Button>
          <Button onClick={onCancel}>Keep playing</Button>
        </div>
      </div>
    </div>
  );
}
