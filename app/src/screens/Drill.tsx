import { useCallback, useEffect, useState } from 'react';
import { api, type Board as BoardData, type Home, type DuePair } from '../api/client';
import { expected, pairs } from '../format';
import { TopBar } from '../App';
import { Board } from '../components/Board';

/** `N` sticks: the same number gets typed every morning. */
function useSticky(key: string, fallback: number) {
  const [value, setValue] = useState(() => Number(localStorage.getItem(key) ?? fallback));
  useEffect(() => {
    localStorage.setItem(key, String(value));
  }, [key, value]);
  return [value, setValue] as const;
}

/**
 * A run is one `GET /draw/boards?n=` — all `N` boards arrive together and are
 * held here, so confirming goes straight to the next without a refetch and a run
 * is worked to its end whatever happens to the date meanwhile. The turned date
 * shows up when the run ends and the fork reloads `/home`.
 */
type Run = { kind: 'boards'; boards: BoardData[]; at: number } | { kind: 'roll'; due: DuePair[] };

/** The two screens of a morning — design/app/Drilling.md. */
export function Drill({ onHome }: { onHome: () => void }) {
  // `GET /home` rather than `GET /draw`: the fork shows the corpus and the
  // expectation as well as the draw, and only /home carries them — see
  // design/api/API.md#the-drill-loop.
  const [home, setHome] = useState<Home | null>(null);
  const [run, setRun] = useState<Run | null>(null);
  const [nBoards, setNBoards] = useSticky('memnasium.n.boards', 3);
  const [nRoll, setNRoll] = useSticky('memnasium.n.roll', 10);

  const load = useCallback(() => {
    void api.home().then(setHome);
  }, []);

  useEffect(load, [load]);

  const draw = home?.draw ?? null;

  if (run) {
    const back = () => {
      setRun(null);
      load();
    };
    if (run.kind === 'roll') {
      return (
        <div className="screen">
          <TopBar title="Drill" onHome={onHome} />
          <Board
            title="The roll"
            pairCount={run.due.length}
            position=""
            due={run.due}
            context={[]}
            onConfirmed={back}
            onAbandoned={back}
          />
        </div>
      );
    }
    const board = run.boards[run.at];
    return (
      <div className="screen">
        <TopBar title="Drill" onHome={onHome} />
        <Board
          key={board.group_id}
          title={board.group_name}
          pairCount={board.pair_count}
          position={`board ${run.at + 1} of ${run.boards.length}`}
          due={board.due}
          context={board.context}
          onConfirmed={() => {
            // Confirming goes straight to the next board of the run.
            if (run.at + 1 < run.boards.length) setRun({ ...run, at: run.at + 1 });
            else back();
          }}
          // A refused confirm has nothing to retry, so the only way on is back
          // to the fork — design/app/Drilling.md#a-refused-confirm.
          onAbandoned={back}
        />
      </div>
    );
  }

  return (
    <div className="screen">
      <TopBar title="Drill" onHome={onHome} />
      {!draw ? (
        <div className="panel">
          {/* Until today is built the fork is not blank: this is the number that
              says whether the morning is ten minutes or an hour, and it is worth
              looking at after a day of wordsmithing. Held back until `home` has
              actually arrived — `0 pairs · ~0 expected` is a confident lie about
              the corpus, not a loading state. */}
          {home && (
            <div className="muted">
              {pairs(home.pairs)} · {expected(home.expected ?? 0)}
            </div>
          )}
          <button
            className="primary"
            onClick={() => {
              void api.buildDraw().then(load);
            }}
          >
            Build today&apos;s draw
          </button>
        </div>
      ) : (
        <div className="panel">
          {/* `drawn` and `expected` are the same draw's outcome and prediction:
              the expectation is the one frozen at that build, not a fresh sum. */}
          {/* No date: the built state is today's by definition. */}
          <div className="label">
            The draw — {draw.drawn} drawn · {expected(draw.expected)}
          </div>
          {draw.due === 0 ? (
            <p className="muted">none left</p>
          ) : (
            <div className="counts">
              <span className="n">{draw.due}</span>
              <span>due pairs</span>
              <span className="n">{draw.boards}</span>
              <span>
                boards{' '}
                <input
                  aria-label="how many boards"
                  style={{ width: '4em', display: 'inline-block' }}
                  value={nBoards}
                  onChange={(e) => setNBoards(Number(e.target.value) || 1)}
                />{' '}
                <button
                  disabled={draw.boards === 0}
                  onClick={() => {
                    void api
                      .boards(nBoards)
                      .then((boards) => setRun({ kind: 'boards', boards, at: 0 }));
                  }}
                >
                  Work boards
                </button>
              </span>
              <span className="n">{draw.roll}</span>
              <span>
                on the roll{' '}
                <input
                  aria-label="how many roll pairs"
                  style={{ width: '4em', display: 'inline-block' }}
                  value={nRoll}
                  onChange={(e) => setNRoll(Number(e.target.value) || 1)}
                />{' '}
                <button
                  disabled={draw.roll === 0}
                  onClick={() => {
                    void api.roll(nRoll).then((batch) => setRun({ kind: 'roll', due: batch.due }));
                  }}
                >
                  Work the roll
                </button>
              </span>
            </div>
          )}
          {/* No Build button: today has a draw, so there is no way to draw again
              until tomorrow — design/app/Drilling.md#decisions. */}
          {/* The live corpus, which does not move during a morning. */}
          {home && <div className="muted">{pairs(home.pairs)}</div>}
        </div>
      )}
    </div>
  );
}
