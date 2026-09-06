import { describe, expect, it, vi } from 'vitest';
import { render, screen } from '@testing-library/react';
import { Home } from '../screens/Home';
import { Drill } from '../screens/Drill';
import { api, type DrawSummary, type Home as HomeCounts } from '../api/client';

vi.mock('better-react-mathjax', () => ({
  MathJax: ({ children }: { children: React.ReactNode }) => <span>{children}</span>,
  MathJaxContext: ({ children }: { children: React.ReactNode }) => <>{children}</>,
}));

/** `day` is always today's when a draw is present — design/api/API.md. */
const draw = (over: Partial<DrawSummary> = {}): DrawSummary => ({
  day: '2026-09-05',
  drawn: 118,
  expected: 87.4,
  due: 34,
  boards: 6,
  roll: 4,
  ...over,
});

/** `expected` at the top level is set only while today has no draw. */
const homeCounts = (d: DrawSummary | null): HomeCounts => ({
  ungrouped_notes: 0,
  placements_without_pairs: 0,
  placements_stale: 0,
  pairs: 1204,
  expected: d ? null : 87.4,
  draw: d,
});

function homeWith(d: DrawSummary | null) {
  vi.spyOn(api, 'home').mockResolvedValue(homeCounts(d));
  render(<Home onGo={vi.fn()} />);
}

function drillWith(d: DrawSummary | null) {
  vi.spyOn(api, 'home').mockResolvedValue(homeCounts(d));
  render(<Drill onHome={vi.fn()} />);
}

describe('the draw on Home', () => {
  it('offers no Build once today has a draw', async () => {
    // app/Home.md — the button is gone until tomorrow
    homeWith(draw());
    expect(await screen.findByText(/118 drawn/)).toBeInTheDocument();
    expect(screen.queryByRole('button', { name: /Build/ })).not.toBeInTheDocument();
  });

  it('carries no date on any of its three states', async () => {
    // app/Home.md — the line is always about today, so saying so would be noise
    homeWith(draw());
    expect(await screen.findByText(/118 drawn/)).toBeInTheDocument();
    expect(screen.queryByText(/Sep/)).not.toBeInTheDocument();
  });

  it('reads a finished draw as built, not as unbuilt', async () => {
    // Data.md#the-draw — the pathological case the marker closes
    homeWith(draw({ due: 0, boards: 0, roll: 0 }));
    expect(await screen.findByText(/none left/)).toBeInTheDocument();
    expect(screen.queryByText(/not built yet/)).not.toBeInTheDocument();
    expect(screen.queryByRole('button', { name: /Build/ })).not.toBeInTheDocument();
  });

  it('says not built yet whenever today has no draw', async () => {
    // Whether none was ever built or the last one was yesterday — the leftovers
    // are stranded and are not counted here.
    homeWith(null);
    expect(await screen.findByText('not built yet')).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /Build/ })).toBeInTheDocument();
  });
});

describe('the drill fork', () => {
  it('offers no way to draw again once today is worked to the end', async () => {
    drillWith(draw({ due: 0, boards: 0, roll: 0 }));
    expect(await screen.findByText(/118 drawn/)).toBeInTheDocument();
    expect(screen.getByText('none left')).toBeInTheDocument();
    expect(screen.queryByRole('button', { name: /Build/ })).not.toBeInTheDocument();
    expect(screen.queryByRole('button', { name: 'Work boards' })).not.toBeInTheDocument();
  });

  it('shows the pre-build screen when today has no draw, whatever was built before', async () => {
    // app/Drilling.md — an earlier draw's leftovers appear in neither state
    drillWith(null);
    expect(await screen.findByRole('button', { name: /Build/ })).toBeInTheDocument();
    expect(screen.queryByRole('button', { name: 'Work boards' })).not.toBeInTheDocument();
  });

  it('carries no date on the built state', async () => {
    drillWith(draw());
    expect(await screen.findByText(/118 drawn/)).toBeInTheDocument();
    expect(screen.queryByText(/Sep/)).not.toBeInTheDocument();
  });
});

describe('the corpus and the expectation', () => {
  it('shows the expectation with a ~, because it is a mean and not a count', async () => {
    // app/Home.md#decisions
    homeWith(draw());
    expect(await screen.findByText(/~87 expected/)).toBeInTheDocument();
  });

  it('predicts the build about to happen while today has no draw', async () => {
    homeWith(null);
    expect(await screen.findByText(/not built yet/)).toBeInTheDocument();
    expect(screen.getByText(/~87 expected/)).toBeInTheDocument();
  });

  it('keeps the live corpus on screen on Home', async () => {
    homeWith(draw());
    expect(await screen.findByText('1,204 pairs')).toBeInTheDocument();
  });

  it('is not a blank fork before the day is built', async () => {
    // app/Drilling.md#decisions — the pre-build screen is not blank
    drillWith(null);
    expect(await screen.findByText(/1,204 pairs · ~87 expected/)).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /Build/ })).toBeInTheDocument();
  });

  it("sits the draw's expectation beside what it drew", async () => {
    drillWith(draw());
    expect(await screen.findByText(/118 drawn · ~87 expected/)).toBeInTheDocument();
    expect(screen.getByText('1,204 pairs')).toBeInTheDocument();
  });

  it('says nothing about the corpus until /home has answered', async () => {
    // app/Home.md — `0 pairs` in flight is a false statement, not a loading state
    vi.spyOn(api, 'home').mockReturnValue(new Promise(() => {}));
    render(<Home onGo={vi.fn()} />);
    expect(await screen.findByText('not built yet')).toBeInTheDocument();
    expect(screen.queryByText(/0 pairs/)).not.toBeInTheDocument();
    expect(screen.queryByText(/expected/)).not.toBeInTheDocument();
  });

  it('says nothing about the corpus on the fork until /home has answered', async () => {
    vi.spyOn(api, 'home').mockReturnValue(new Promise(() => {}));
    render(<Drill onHome={vi.fn()} />);
    expect(await screen.findByRole('button', { name: /Build/ })).toBeInTheDocument();
    expect(screen.queryByText(/0 pairs/)).not.toBeInTheDocument();
    expect(screen.queryByText(/expected/)).not.toBeInTheDocument();
  });
});
