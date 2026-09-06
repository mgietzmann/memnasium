import { useCallback, useEffect, useState } from 'react';
import { api, type Home as HomeCounts } from '../api/client';
import { expected, pairs } from '../format';
import { TopBar, type Screen } from '../App';

/**
 * The front page: what is waiting, whether today's draw exists, and the two
 * doors — design/app/Home.md. Nothing here links to a skill.
 */
export function Home({ onGo }: { onGo: (screen: Screen) => void }) {
  const [home, setHome] = useState<HomeCounts | null>(null);

  const load = useCallback(() => {
    api
      .home()
      .then(setHome)
      .catch(() => setHome(null));
  }, []);

  useEffect(load, [load]);

  const build = () => {
    void api.buildDraw().then(load);
  };

  return (
    <div className="screen">
      <TopBar title="" />

      <div className="panel">
        <div className="label">The draw</div>
        <div>
          {/*
            The line reads today's draw, and carries no date: it is always about
            today, so saying so would be noise — see design/app/Home.md.
          */}
          {home?.draw ? (
            <>
              {home.draw.drawn} drawn
              {/*
                The expectation shown is the one frozen on this draw, never a
                fresh sum: `118 drawn · ~87 expected` is a claim about one draw.
              */}
              <span className="muted"> · {expected(home.draw.expected)}</span>
              {home.draw.due === 0 ? (
                <span className="muted"> · none left</span>
              ) : (
                <>
                  {' · '}
                  {home.draw.due} due · {home.draw.boards} boards · {home.draw.roll} on the roll
                </>
              )}
            </>
          ) : (
            <>
              {/* What a day opens on whether the last draw was yesterday or in
                  March. Anything left of that draw is stranded: not counted here,
                  not offered by Drill, and swept by the build. */}
              <span className="muted">not built yet</span>
              {/* A prediction of the build about to happen, which moves as notes
                  are wordsmithed into pairs. */}
              {home && <span className="muted"> · {expected(home.expected ?? 0)}</span>}
            </>
          )}
          {!home?.draw && (
            <>
              {' '}
              <button className="primary" onClick={build}>
                Build today&apos;s draw
              </button>
            </>
          )}
        </div>
        {/* The live corpus: the only line here that says how big the thing being
            practised actually is. It sits in the draw's own panel — see
            design/app/Home.md#layout — does not move during a morning, and is
            held back until `home` has arrived rather than reading `0 pairs`. */}
        {home && <div className="muted">{pairs(home.pairs)}</div>}
      </div>

      <div className="panel">
        <div className="label">waiting on you</div>
        <div className="counts">
          {/* A count of zero is shown as zero. The absence of work is information. */}
          <span className="n">{home?.ungrouped_notes ?? 0}</span>
          <span>notes not yet grouped</span>
          <span className="n">{home?.placements_without_pairs ?? 0}</span>
          <span>placements with no pairs</span>
          <span className="n">{home?.placements_stale ?? 0}</span>
          <span>placements with stale pairs</span>
        </div>
      </div>

      <div className="doors">
        <button onClick={() => onGo('entry')}>Enter a note</button>
        <button onClick={() => onGo('drill')}>Drill</button>
      </div>
    </div>
  );
}
