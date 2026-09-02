// One card per game, each showing whatever state that game reports. Play tables are per-game, so
// there is no shared query — the list is a row of answers, not one (design/app/Navigation.md).

import { useEffect, useState } from 'react';

import { api } from '../api/client';
import type { KinState } from '../api/types';
import { kinStateLine } from '../kinDay';

export interface GamesProps {
  onOpen: () => void;
}

export function Games({ onOpen }: GamesProps) {
  const [state, setState] = useState<KinState | null>(null);

  useEffect(() => {
    void api.kinState().then(setState);
  }, []);

  return (
    <div className="games">
      <button type="button" className="game-card" onClick={onOpen}>
        <h2>Kin</h2>
        <p className="common">{kinStateLine(state)}</p>
      </button>
    </div>
  );
}
