import { useEffect, useState } from 'react';
import { api, type Miss } from '../api/client';
import { day as writtenOut } from '../format';
import { TopBar } from '../App';
import { Tex } from '../components/Tex';

/** Pairs that were on the roll have no group, so they sit under a final rule. */
const THE_ROLL = 'The roll';

/**
 * The misses of one group, in the order the boards were worked.
 *
 * `miss` stores a day and nothing finer, so `id` is the only thing that orders
 * a sitting — design/app/Review.md#order.
 */
type Rule = { id: number | null; name: string; misses: Miss[] };

/**
 * Groups the misses by their group, name ascending with `The roll` always last,
 * and each group's misses by `id` ascending.
 *
 * Keyed on `group_id`, never on the name: `groups.name` carries no unique
 * constraint, so two groups sharing one would otherwise be merged into a single
 * rule — and a group actually called `The roll` would swallow the roll's misses
 * and sort last. The name is for display. `null` is the roll itself.
 *
 * The route answers newest first; a single day is short and the app re-sorts it
 * — design/api/API.md#the-record.
 */
export function byGroup(misses: Miss[]): Rule[] {
  const rules = new Map<number | null, Rule>();
  for (const miss of misses) {
    const held = rules.get(miss.group_id);
    if (held) held.misses.push(miss);
    else
      rules.set(miss.group_id, {
        id: miss.group_id,
        name: miss.group_name ?? THE_ROLL,
        misses: [miss],
      });
  }
  return [...rules.values()]
    .map((rule) => ({ ...rule, misses: [...rule.misses].sort((a, b) => a.id - b.id) }))
    .sort((a, b) => {
      if (a.id === null) return 1;
      if (b.id === null) return -1;
      // Two groups may share a name, and a tie left to the route's ordering
      // would put the same page in a different order tomorrow.
      return a.name.localeCompare(b.name) || a.id - b.id;
    });
}

/**
 * Everything blown in the last drill, by group — design/app/Review.md.
 *
 * Read-only over the record. Nothing here writes, which is why a drill in
 * progress is reviewable. There are no controls: it is a page to read.
 */
export function Review({ onHome }: { onHome: () => void }) {
  // Held back until the route has answered: `Nothing missed.` while the request
  // is in flight is a confident false statement rather than a loading state.
  const [misses, setMisses] = useState<Miss[] | null>(null);

  useEffect(() => {
    api
      .lastDrillMisses()
      .then(setMisses)
      // A route that refuses, or a server that is not up, is not a clean
      // morning: `[]` would render `Nothing missed.` over a failure, which is
      // the same confident false statement the loading state is held back for.
      .catch(() => setMisses(null));
  }, []);

  const rules = misses ? byGroup(misses) : [];

  return (
    <div className="screen">
      <TopBar title="Review" onHome={onHome} />

      {misses !== null &&
        (misses.length === 0 ? (
          /* No date. The day rides on the miss rows, so an empty answer has no
             day to name — design/app/Review.md#nothing-missed. */
          <p>Nothing missed.</p>
        ) : (
          <>
            {/* A count and the day it belongs to, written out: the page is about
                one past day, so the date is stated rather than assumed. */}
            <p className="missed-on">
              {misses.length} missed on {writtenOut(misses[0].day)}
            </p>
            {rules.map((rule) => (
              <section key={rule.id ?? THE_ROLL}>
                {/* Group names are rules, not panels: the page is read top to
                    bottom in one pass and boxes would break it into things to
                    be visited. */}
                <h2 className="rule">{rule.name}</h2>
                {rule.misses.map((miss) => (
                  <Missed key={miss.id} miss={miss} />
                ))}
              </section>
            ))}
          </>
        ))}
    </div>
  );
}

/**
 * The question, then the truth and what was typed, split by the same rule a
 * board's columns use — design/app/Review.md#a-miss.
 *
 * No glyphs: every row on this page is a miss, so a `✗` on each one carries
 * nothing the page title has not already said.
 */
function Missed({ miss }: { miss: Miss }) {
  return (
    <div className="miss">
      <div className="question">
        <Tex>{miss.question}</Tex>
      </div>
      {/* The truth is the thing being studied, so it leads; the mistake is the
          annotation. On a board the order is reversed. */}
      <div className="answer">
        <Tex>{miss.answer}</Tex>
      </div>
      <div className="typed">
        <span className="muted">you said</span> <Tex>{miss.user_answer}</Tex>
      </div>
      {/* Shown even when what was typed matches: a `miss` row does not record
          which of the two boxes Claude failed. */}
      <div className="answer source">
        {miss.source.author} {miss.source.year}
      </div>
      <div className="typed source">
        <span className="muted">you said</span> {miss.user_source}
      </div>
    </div>
  );
}
