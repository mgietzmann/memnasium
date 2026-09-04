import { useMemo, useState } from 'react';
import { api, type ContextPair, type DuePair, type Verdict } from '../api/client';
import { Tex } from './Tex';

/**
 * One board, in its three states: answering, graded, confirmed.
 *
 * design/app/Drilling.md#a-board. A roll batch is this with `context` empty —
 * not a second screen.
 */
export function Board({
  title,
  pairCount,
  position,
  due,
  context,
  onConfirmed,
}: {
  title: string;
  pairCount: number | null;
  position: string;
  due: DuePair[];
  context: ContextPair[];
  onConfirmed: () => void;
}) {
  const [typed, setTyped] = useState<Record<number, { answer: string; source: string }>>({});
  const [verdicts, setVerdicts] = useState<Verdict[] | null>(null);
  const [contested, setContested] = useState<Set<number>>(new Set());
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const box = (id: number) => typed[id] ?? { answer: '', source: '' };

  // Submit is disabled until every box on the left has something in it.
  const complete = due.every((p) => box(p.id).answer.trim() && box(p.id).source.trim());

  const byId = useMemo(
    () => new Map((verdicts ?? []).map((v) => [v.recall_pair_id, v])),
    [verdicts],
  );

  const missed = (v: Verdict) => !(v.answer_correct && v.source_correct);

  const submit = () => {
    setBusy(true);
    setError(null);
    api
      .grade(
        due.map((p) => ({
          recall_pair_id: p.id,
          user_answer: box(p.id).answer,
          user_source: box(p.id).source,
        })),
      )
      .then((r) => setVerdicts(r.verdicts))
      .catch((e: Error) => setError(e.message))
      .finally(() => setBusy(false));
  };

  const confirm = () => {
    setBusy(true);
    setError(null);
    api
      .confirm(
        due.map((p) => {
          const verdict = byId.get(p.id);
          const correct = verdict ? !missed(verdict) || contested.has(p.id) : false;
          return {
            recall_pair_id: p.id,
            correct,
            user_answer: box(p.id).answer,
            user_source: box(p.id).source,
          };
        }),
      )
      .then(onConfirmed)
      .catch((e: Error) => setError(e.message))
      .finally(() => setBusy(false));
  };

  return (
    <div className={context.length ? '' : 'roll'}>
      <div className="topbar">
        <h1>
          {title}
          {pairCount !== null && <span className="muted"> · {pairCount} pairs</span>}
        </h1>
        <span className="label">{position}</span>
      </div>

      <div className="board">
        <div className="due-col">
          <div className="label">
            due <span>{due.length}</span>
          </div>
          {due.map((pair) => {
            const verdict = byId.get(pair.id);
            return (
              <div className="pair" key={pair.id}>
                <div className="question">
                  <Tex>{pair.question}</Tex>
                </div>
                {!verdict ? (
                  <>
                    <input
                      className="box"
                      aria-label={`answer for pair ${pair.id}`}
                      placeholder="answer"
                      value={box(pair.id).answer}
                      onChange={(e) =>
                        setTyped((t) => ({
                          ...t,
                          [pair.id]: { ...box(pair.id), answer: e.target.value },
                        }))
                      }
                    />
                    <input
                      className="box"
                      aria-label={`source for pair ${pair.id}`}
                      placeholder="source"
                      value={box(pair.id).source}
                      onChange={(e) =>
                        setTyped((t) => ({
                          ...t,
                          [pair.id]: { ...box(pair.id), source: e.target.value },
                        }))
                      }
                    />
                  </>
                ) : (
                  <Graded
                    verdict={verdict}
                    typed={box(pair.id)}
                    contested={contested.has(pair.id)}
                    onContest={() =>
                      setContested((prior) => {
                        const next = new Set(prior);
                        next.add(pair.id);
                        return next;
                      })
                    }
                  />
                )}
              </div>
            );
          })}

          {error && <p className="verdict missed">{error}</p>}

          {!verdicts ? (
            <button className="primary" disabled={!complete || busy} onClick={submit}>
              Submit
            </button>
          ) : (
            <button className="primary" disabled={busy} onClick={confirm}>
              Confirm
            </button>
          )}
        </div>

        {context.length > 0 && (
          <div className="context-col">
            <div className="label">
              context <span>{context.length}</span>
            </div>
            {context.map((pair) => (
              <div className="context-pair" key={pair.id}>
                <div>
                  <Tex>{pair.question}</Tex>
                </div>
                <div className="answer">
                  <Tex>{pair.answer}</Tex>
                </div>
                <div className="source">
                  {pair.source.author} {pair.source.year}
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}

/**
 * A graded pair. Each box carries its own glyph and rule, so turning off every
 * colour still tells them apart — design/standards/Style.md#pair-states.
 */
function Graded({
  verdict,
  typed,
  contested,
  onContest,
}: {
  verdict: Verdict;
  typed: { answer: string; source: string };
  contested: boolean;
  onContest: () => void;
}) {
  const answerOk = verdict.answer_correct || contested;
  const sourceOk = verdict.source_correct || contested;
  return (
    <div>
      <div className={`verdict ${answerOk ? 'correct' : 'missed'}`}>
        <div className="said">
          you said <Tex>{typed.answer}</Tex>
        </div>
        <div>
          <span className="glyph">{answerOk ? '✓' : '✗'}</span>
          {answerOk ? 'answer' : 'missed'}
          {!answerOk && verdict.right_answer && (
            <span className="truth">
              {' '}
              → <Tex>{verdict.right_answer}</Tex>
            </span>
          )}
        </div>
      </div>
      <div className={`verdict ${sourceOk ? 'correct' : 'missed'}`}>
        <div className="said">you said {typed.source}</div>
        <div>
          <span className="glyph">{sourceOk ? '✓' : '✗'}</span>
          source
          {!sourceOk && verdict.right_source && (
            <span className="truth"> → {verdict.right_source}</span>
          )}
        </div>
      </div>
      {!contested && !(verdict.answer_correct && verdict.source_correct) && (
        <button className="link" onClick={onContest}>
          contest
        </button>
      )}
    </div>
  );
}
