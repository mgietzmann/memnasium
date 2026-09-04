import { describe, expect, it, vi } from 'vitest';
import { render, screen } from '@testing-library/react';
import { Home } from '../screens/Home';
import { Drill } from '../screens/Drill';
import { api, type DrawSummary, type Home as HomeCounts } from '../api/client';
import { todayIso } from '../api/day';

vi.mock('better-react-mathjax', () => ({
  MathJax: ({ children }: { children: React.ReactNode }) => <span>{children}</span>,
  MathJaxContext: ({ children }: { children: React.ReactNode }) => <>{children}</>,
}));

const draw = (over: Partial<DrawSummary> = {}): DrawSummary => ({
  day: todayIso(),
  drawn: 118,
  expected: 87.4,
  due: 34,
  boards: 6,
  roll: 4,
  ...over,
});

/** `expected` at the top level is set only when no draw has ever been built. */
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
  it('offers Build only when today has no draw of its own', async () => {
    // app/Home.md — Build is offered when the current draw is not today's
    homeWith(draw());
    expect(await screen.findByText(/118 drawn/)).toBeInTheDocument();
    expect(screen.queryByRole('button', { name: /Build/ })).not.toBeInTheDocument();
  });

  it('reads a finished draw as built, not as unbuilt', async () => {
    // Data.md#the-draw — the pathological case the marker closes
    homeWith(draw({ due: 0, boards: 0, roll: 0 }));
    expect(await screen.findByText(/none left/)).toBeInTheDocument();
    expect(screen.queryByText(/not built yet/)).not.toBeInTheDocument();
    expect(screen.queryByRole('button', { name: /Build/ })).not.toBeInTheDocument();
  });

  it('shows a carried-over draw with its date and a Build button beside it', async () => {
    homeWith(draw({ day: '2026-09-01' }));
    expect(await screen.findByText(/1 Sep/)).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /Build/ })).toBeInTheDocument();
  });

  it('says not built yet only when none has ever been built', async () => {
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

  it('keeps a Build button on a draw carried over from an earlier day', async () => {
    drillWith(draw({ day: '2026-09-01' }));
    expect(await screen.findByText(/1 Sep/)).toBeInTheDocument();
    expect(screen.getByRole('button', { name: 'Work boards' })).toBeEnabled();
    expect(screen.getByRole('button', { name: /Build/ })).toBeInTheDocument();
  });
});

describe('the corpus and the expectation', () => {
  it('shows the expectation with a ~, because it is a mean and not a count', async () => {
    // app/Home.md#decisions
    homeWith(draw());
    expect(await screen.findByText(/~87 expected/)).toBeInTheDocument();
  });

  it('predicts the build about to happen when none has ever been built', async () => {
    homeWith(null);
    expect(await screen.findByText(/not built yet/)).toBeInTheDocument();
    expect(screen.getByText(/~87 expected/)).toBeInTheDocument();
  });

  it('keeps the live corpus on screen on Home', async () => {
    homeWith(draw());
    expect(await screen.findByText('1,204 pairs')).toBeInTheDocument();
  });

  it('is not a blank fork before the first build', async () => {
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
