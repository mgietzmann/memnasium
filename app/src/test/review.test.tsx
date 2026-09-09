import { describe, expect, it, vi, beforeEach } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import { Review, byGroup } from '../screens/Review';
import { api, type Miss } from '../api/client';

vi.mock('better-react-mathjax', () => ({
  MathJax: ({ children }: { children: React.ReactNode }) => <span>{children}</span>,
  MathJaxContext: ({ children }: { children: React.ReactNode }) => <>{children}</>,
}));

/** Reading back the last drill's misses — design/app/Review.md. */

const duffy = { id: 1, author: 'Duffy', year: 2010, publication: null };

function miss(over: Partial<Miss> = {}): Miss {
  return {
    id: 1,
    recall_pair_id: 10,
    day: '2026-09-08',
    user_answer: '130 mm',
    user_source: 'Duffy 2012',
    question: 'Puget Sound, inshore?',
    answer: '70 mm',
    source: duffy,
    group_id: 1,
    group_name: 'Onset of piscivory',
    ...over,
  };
}

beforeEach(() => {
  vi.restoreAllMocks();
});

function show(misses: Miss[]) {
  vi.spyOn(api, 'lastDrillMisses').mockResolvedValue(misses);
  return render(<Review onHome={vi.fn()} />);
}

describe('order', () => {
  it('sorts groups by name and keeps the roll last', () => {
    // design/app/Review.md#order
    const rules = byGroup([
      miss({ id: 3, group_id: null, group_name: null }),
      miss({ id: 2, group_id: 2, group_name: 'Smolt outmigration timing' }),
      miss({ id: 1 }),
    ]);
    expect(rules.map((r) => r.name)).toEqual([
      'Onset of piscivory',
      'Smolt outmigration timing',
      'The roll',
    ]);
  });

  it('keeps two groups of one name apart, and the roll last whatever it is called', () => {
    // `groups.name` has no unique constraint, so the id is what identifies a rule.
    const rules = byGroup([
      miss({ id: 4, group_id: null, group_name: null }),
      miss({ id: 3, group_id: 3, group_name: 'The roll' }),
      miss({ id: 2, group_id: 2, group_name: 'Onset of piscivory' }),
      miss({ id: 1 }),
    ]);
    expect(rules.map((r) => [r.id, r.name])).toEqual([
      [1, 'Onset of piscivory'],
      [2, 'Onset of piscivory'],
      [3, 'The roll'],
      [null, 'The roll'],
    ]);
  });

  it('walks a sitting forwards, though the route answers newest first', () => {
    // design/api/API.md#the-record — a single day is short and the app re-sorts it
    const [rule] = byGroup([miss({ id: 9 }), miss({ id: 4 }), miss({ id: 7 })]);
    expect(rule.misses.map((m) => m.id)).toEqual([4, 7, 9]);
  });
});

describe('the page', () => {
  it('heads with the count and the day, written out', async () => {
    show([miss(), miss({ id: 2, recall_pair_id: 11 })]);
    expect(await screen.findByText('2 missed on 8 September')).toBeInTheDocument();
  });

  it('shows the truth and what was typed, in both boxes', async () => {
    // Both are shown even when one matched: a miss row does not say which failed.
    show([miss({ user_source: 'Duffy 2010' })]);
    expect(await screen.findByText('70 mm')).toBeInTheDocument();
    expect(screen.getByText('130 mm')).toBeInTheDocument();
    // The source row is shown even though what was typed matched.
    expect(screen.getAllByText('Duffy 2010')).toHaveLength(2);
    expect(screen.getAllByText('you said')).toHaveLength(2);
  });

  it('carries no glyphs', async () => {
    // design/app/Review.md#a-miss — every row is a miss, so a ✗ says nothing
    const { container } = show([miss()]);
    await screen.findByText('70 mm');
    expect(container.textContent).not.toContain('✗');
  });

  it('says nothing missed, without a date', async () => {
    // design/app/Review.md#nothing-missed
    show([]);
    expect(await screen.findByText('Nothing missed.')).toBeInTheDocument();
  });

  it('says nothing when the route refuses, rather than nothing missed', async () => {
    // A failure is not a clean morning — the same reason the loading state holds.
    vi.spyOn(api, 'lastDrillMisses').mockRejectedValue(new Error('no server'));
    render(<Review onHome={vi.fn()} />);
    await waitFor(() => expect(api.lastDrillMisses).toHaveBeenCalled());
    expect(screen.queryByText('Nothing missed.')).not.toBeInTheDocument();
  });

  it('says nothing at all until the route has answered', async () => {
    // A `Nothing missed.` while the request is in flight is a false statement.
    show([]);
    expect(screen.queryByText('Nothing missed.')).not.toBeInTheDocument();
    await screen.findByText('Nothing missed.');
  });
});
