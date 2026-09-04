import { describe, expect, it, vi } from 'vitest';
import { render, screen } from '@testing-library/react';
import { Home } from '../screens/Home';
import { Drill } from '../screens/Drill';
import { api, type DrawSummary } from '../api/client';
import { todayIso } from '../api/day';

vi.mock('better-react-mathjax', () => ({
  MathJax: ({ children }: { children: React.ReactNode }) => <span>{children}</span>,
  MathJaxContext: ({ children }: { children: React.ReactNode }) => <>{children}</>,
}));

const draw = (over: Partial<DrawSummary> = {}): DrawSummary => ({
  day: todayIso(),
  drawn: 118,
  due: 34,
  boards: 6,
  roll: 4,
  ...over,
});

function homeWith(d: DrawSummary | null) {
  vi.spyOn(api, 'home').mockResolvedValue({
    ungrouped_notes: 0,
    placements_without_pairs: 0,
    placements_stale: 0,
    draw: d,
  });
  render(<Home onGo={vi.fn()} />);
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
    vi.spyOn(api, 'draw').mockResolvedValue(draw({ due: 0, boards: 0, roll: 0 }));
    render(<Drill onHome={vi.fn()} />);
    expect(await screen.findByText(/118 drawn/)).toBeInTheDocument();
    expect(screen.getByText('none left')).toBeInTheDocument();
    expect(screen.queryByRole('button', { name: /Build/ })).not.toBeInTheDocument();
    expect(screen.queryByRole('button', { name: 'Work boards' })).not.toBeInTheDocument();
  });

  it('keeps a Build button on a draw carried over from an earlier day', async () => {
    vi.spyOn(api, 'draw').mockResolvedValue(draw({ day: '2026-09-01' }));
    render(<Drill onHome={vi.fn()} />);
    expect(await screen.findByText(/1 Sep/)).toBeInTheDocument();
    expect(screen.getByRole('button', { name: 'Work boards' })).toBeEnabled();
    expect(screen.getByRole('button', { name: /Build/ })).toBeInTheDocument();
  });
});
