import { describe, expect, it, vi } from 'vitest';
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { Entry } from '../screens/Entry';
import { api, type Note } from '../api/client';

vi.mock('better-react-mathjax', () => ({
  MathJax: ({ children }: { children: React.ReactNode }) => <span>{children}</span>,
  MathJaxContext: ({ children }: { children: React.ReactNode }) => <>{children}</>,
}));

const riddell = { id: 1, author: 'Riddell', year: 2018, publication: 'Chinook in SE Alaska' };

const note = (over: Partial<Note> = {}): Note => ({
  id: 517,
  statement: 'Yukon fish transition at 85-90 mm',
  created_on: '2026-09-03',
  source: riddell,
  placed: false,
  ...over,
});

async function pickSource(user: ReturnType<typeof userEvent.setup>) {
  vi.spyOn(api, 'searchSources').mockResolvedValue([riddell]);
  await user.type(screen.getByLabelText('search sources'), 'ridd');
  await user.click(await screen.findByRole('button', { name: /Riddell 2018/ }));
}

describe('the entry screen', () => {
  it('holds the source pick across a save', async () => {
    // flows/Entry.md — the source is sticky
    const user = userEvent.setup();
    vi.spyOn(api, 'createNote').mockResolvedValue(note());
    render(<Entry onHome={vi.fn()} />);
    await pickSource(user);
    await user.type(screen.getByLabelText('statement'), 'Yukon fish transition at 85-90 mm');
    await user.click(screen.getByRole('button', { name: 'Save' }));
    expect(await screen.findByText(/Riddell 2018/)).toBeInTheDocument();
    expect(screen.getByLabelText('statement')).toHaveValue('');
  });

  it('will not save without a source', () => {
    render(<Entry onHome={vi.fn()} />);
    expect(screen.getByRole('button', { name: 'Save' })).toBeDisabled();
  });

  it('offers create only under an empty search result', async () => {
    // app/Entry.md#decisions — a link under the empty result, never a button beside the box
    const user = userEvent.setup();
    vi.spyOn(api, 'searchSources').mockResolvedValue([]);
    render(<Entry onHome={vi.fn()} />);
    expect(screen.queryByRole('button', { name: 'create this source' })).not.toBeInTheDocument();
    await user.type(screen.getByLabelText('search sources'), 'zzz');
    expect(await screen.findByRole('button', { name: 'create this source' })).toBeInTheDocument();
  });

  it('hides the edit and delete controls on a note that has a placement', async () => {
    // app/Entry.md#entered-today
    const user = userEvent.setup();
    vi.spyOn(api, 'createNote').mockResolvedValue(note({ placed: true }));
    render(<Entry onHome={vi.fn()} />);
    await pickSource(user);
    await user.type(screen.getByLabelText('statement'), 'anything');
    await user.click(screen.getByRole('button', { name: 'Save' }));
    expect(await screen.findByText('517')).toBeInTheDocument();
    expect(screen.queryByLabelText('edit note 517')).not.toBeInTheDocument();
    expect(screen.queryByLabelText('delete note 517')).not.toBeInTheDocument();
  });

  it('offers the controls on an ungrouped note', async () => {
    const user = userEvent.setup();
    vi.spyOn(api, 'createNote').mockResolvedValue(note());
    render(<Entry onHome={vi.fn()} />);
    await pickSource(user);
    await user.type(screen.getByLabelText('statement'), 'anything');
    await user.click(screen.getByRole('button', { name: 'Save' }));
    expect(await screen.findByLabelText('edit note 517')).toBeInTheDocument();
    expect(screen.getByLabelText('delete note 517')).toBeInTheDocument();
  });
});
