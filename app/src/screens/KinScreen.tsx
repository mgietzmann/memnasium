// Playing Kin: a header carrying the day's state, and the board beneath it (design/app/Kin.md).
// The rules underneath are design/games/Kin.md; the calls are design/api/Kin.md.

import { useCallback, useEffect, useState } from 'react';

import { api } from '../api/client';
import type { Board, Card, KinState, Slot as SlotData } from '../api/types';
import { Button } from '../components/Button';
import { Chip } from '../components/Chip';
import { Confirm } from '../components/Confirm';
import { Slot } from '../components/Slot';
import { needsGenerate } from '../kinDay';

type Selection = { kind: 'clade'; value: string } | { kind: 'source'; value: number } | null;
type Fills = Record<string, string | number>;

const SIZES = [2, 3, 4, 5, 6, 8, 10];

function dueSlots(board: Board): SlotData[] {
  return board.cards
    .flatMap((card) => [card.clade, card.src])
    .filter((slot) => slot.state === 'due');
}

/** The board as it reads once every slot is locked — what a completed board shows. */
function completed(board: Board, fills: Fills): Board {
  const lock = (slot: SlotData): SlotData =>
    slot.state === 'locked' ? slot : { ...slot, state: 'locked', value: fills[slot.slot] ?? null };
  return {
    ...board,
    ended: true,
    cards: board.cards.map((card) => ({ ...card, clade: lock(card.clade), src: lock(card.src) })),
  };
}

export function KinScreen() {
  const [state, setState] = useState<KinState | null>(null);
  const [board, setBoard] = useState<Board | null>(null);
  const [ended, setEnded] = useState<Board | null>(null);
  const [fills, setFills] = useState<Fills>({});
  const [selection, setSelection] = useState<Selection>(null);
  const [size, setSize] = useState(3);
  const [confirming, setConfirming] = useState(false);
  const [busy, setBusy] = useState(false);

  const refresh = useCallback(async () => {
    const [next, open] = await Promise.all([api.kinState(), api.openBoard()]);
    setState(next);
    setBoard(open);
  }, []);

  useEffect(() => {
    void refresh();
  }, [refresh]);

  const shown = ended ?? board;

  function fill(slot: SlotData, kind: 'clade' | 'source') {
    if (slot.state === 'locked') return;
    if (fills[slot.slot] !== undefined) {
      setFills((current) =>
        Object.fromEntries(Object.entries(current).filter(([held]) => held !== slot.slot)),
      );
      return;
    }
    if (selection === null || selection.kind !== kind) return;
    setFills((current) => ({ ...current, [slot.slot]: selection.value }));
  }

  async function submit() {
    if (!board) return;
    setBusy(true);
    try {
      const result = await api.submitBoard(fills);
      if (result.complete) {
        setEnded(completed(board, fills));
        setFills({});
      } else {
        const kept: Fills = {};
        for (const [slot, verdict] of Object.entries(result.results)) {
          if (verdict === 'correct' && fills[slot] !== undefined) kept[slot] = fills[slot];
        }
        setFills(kept);
        setBoard(await api.openBoard());
      }
    } finally {
      setBusy(false);
    }
  }

  async function moveOn() {
    setConfirming(false);
    setBusy(true);
    try {
      setEnded(await api.moveOn());
      setFills({});
    } finally {
      setBusy(false);
    }
  }

  async function next() {
    setEnded(null);
    setSelection(null);
    await refresh();
  }

  const complete =
    board !== null && dueSlots(board).every((slot) => fills[slot.slot] !== undefined);
  const left = state?.anchors_left ?? 0;

  return (
    <div className="kin">
      <div className="kin-header">
        <h1>Kin</h1>
        <div className="kin-actions">
          {needsGenerate(state) && (
            <Button
              disabled={busy}
              onClick={() => {
                setBusy(true);
                void api
                  .generateSet()
                  .then(setState)
                  .finally(() => {
                    setBusy(false);
                  });
              }}
            >
              Generate today’s set
            </Button>
          )}
          {!needsGenerate(state) && ended !== null && (
            <Button
              onClick={() => {
                void next();
              }}
            >
              Next
            </Button>
          )}
          {!needsGenerate(state) && ended === null && board !== null && (
            <>
              <span className="common">{left} anchors left</span>
              <Button
                disabled={!complete || busy}
                onClick={() => {
                  void submit();
                }}
              >
                Submit
              </Button>
              <Button
                kind="danger"
                onClick={() => {
                  setConfirming(true);
                }}
              >
                Move on
              </Button>
            </>
          )}
          {!needsGenerate(state) && ended === null && board === null && left > 0 && (
            <>
              <span className="common">{left} anchors left</span>
              <label className="label" htmlFor="group-size">
                group size
              </label>
              <select
                id="group-size"
                className="input input-inline"
                value={size}
                onChange={(event) => {
                  setSize(Number(event.target.value));
                }}
              >
                {SIZES.map((n) => (
                  <option key={n} value={n}>
                    {n}
                  </option>
                ))}
              </select>
              <Button
                disabled={busy}
                onClick={() => {
                  setBusy(true);
                  void api
                    .dealBoard(size)
                    .then(setBoard)
                    .finally(() => {
                      setBusy(false);
                    });
                }}
              >
                Start
              </Button>
            </>
          )}
          {!needsGenerate(state) && ended === null && board === null && left === 0 && (
            <span className="common">done for today</span>
          )}
        </div>
      </div>

      {shown && (
        <div className="board">
          <div className="palette" aria-label="clades">
            {shown.clades.map((clade) => (
              <Chip
                key={clade.name}
                selected={selection?.kind === 'clade' && selection.value === clade.name}
                onClick={() => {
                  setSelection({ kind: 'clade', value: clade.name });
                }}
              >
                <span className="sci">{clade.name}</span>
                {clade.common_name && <span className="common"> {clade.common_name}</span>}
              </Chip>
            ))}
          </div>

          <div className="cards">
            {shown.cards.map((card) => (
              <BoardCard
                key={`${card.clade.slot}/${card.src.slot}`}
                card={card}
                labels={shown.labels}
                fills={fills}
                onClade={() => {
                  fill(card.clade, 'clade');
                }}
                onSource={() => {
                  fill(card.src, 'source');
                }}
              />
            ))}
          </div>

          <div className="pool" aria-label="citations">
            {shown.citations.map((cite) => (
              <Chip
                key={cite.src}
                selected={selection?.kind === 'source' && selection.value === cite.src}
                onClick={() => {
                  setSelection({ kind: 'source', value: cite.src });
                }}
              >
                <span className="cite">{cite.label}</span>
              </Chip>
            ))}
          </div>
        </div>
      )}

      {confirming && (
        <Confirm
          title="Give up this board?"
          detail="Everything not already right counts as missed. The answers are shown afterwards."
          confirmLabel="Move on"
          onConfirm={() => {
            void moveOn();
          }}
          onCancel={() => {
            setConfirming(false);
          }}
        />
      )}
    </div>
  );
}

interface BoardCardProps {
  card: Card;
  labels: Record<string, string>;
  fills: Fills;
  onClade: () => void;
  onSource: () => void;
}

/** One image or one character: a clade slot on top, the payload, a source slot beneath. */
function BoardCard({ card, labels, fills, onClade, onSource }: BoardCardProps) {
  const cladeFill = fills[card.clade.slot];
  const srcFill = fills[card.src.slot];
  const cladeValue = card.clade.state === 'locked' ? card.clade.value : cladeFill;
  const srcValue = card.src.state === 'locked' ? card.src.value : srcFill;

  return (
    <div className="board-card">
      <Slot
        kind="clade"
        state={
          card.clade.state === 'locked' ? 'locked' : cladeFill === undefined ? 'empty' : 'filled'
        }
        value={<span className="sci">{cladeValue}</span>}
        onClick={onClade}
      />
      <div className="board-payload">
        {card.kind === 'image' && card.img_id ? (
          <img src={api.imageUrl(card.img_id)} alt="" />
        ) : (
          <p>{card.text}</p>
        )}
      </div>
      <Slot
        kind="source"
        state={card.src.state === 'locked' ? 'locked' : srcFill === undefined ? 'empty' : 'filled'}
        value={
          <span className="cite">
            {srcValue === undefined || srcValue === null ? '' : labels[String(srcValue)]}
          </span>
        }
        onClick={onSource}
      />
    </div>
  );
}
