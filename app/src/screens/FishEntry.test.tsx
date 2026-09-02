// design/app/Fish.md — explicit create over implicit create, the walk stopping at the first
// known ancestor, and sticky fields with a cleared payload.

import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { beforeEach, describe, expect, it, vi } from 'vitest';

import { FishEntry } from './FishEntry';

const api = {
  searchClades: vi.fn(),
  getClade: vi.fn(),
  searchSources: vi.fn(),
  postCharacter: vi.fn(),
  postImage: vi.fn(),
  imageUrl: (id: string) => `/api/fish/images/${id}`,
};

vi.mock('../api/client', () => ({
  api: new Proxy({}, { get: (_, key: string) => api[key as keyof typeof api] }),
}));

const claudus = {
  name: 'Artificialus claudus',
  common_name: 'spotted claudfish',
  level: 'species' as const,
  ancestors: [
    { name: 'Artificialus', level: 'genus' as const },
    { name: 'Artificialidae', level: 'family' as const },
  ],
};

const brown = { src: 17, author: 'Brown', year: 2014, title: 'Spines', label: 'Brown, 2014' };

beforeEach(() => {
  vi.clearAllMocks();
  api.searchClades.mockResolvedValue([]);
  api.searchSources.mockResolvedValue([]);
  api.getClade.mockResolvedValue(claudus);
});

describe('the entry form', () => {
  it('fills the ancestor chain read-only when a clade matches', async () => {
    // app/Fish.md — the clade block
    api.searchClades.mockResolvedValue([
      { name: claudus.name, common_name: claudus.common_name, level: 'species' },
    ]);
    render(<FishEntry />);
    await userEvent.type(screen.getByLabelText('Clade'), 'claud');
    await userEvent.click(await screen.findByRole('button', { name: /Artificialus claudus/ }));
    expect(await screen.findByText('Artificialidae')).toBeInTheDocument();
    expect(screen.getByText('Artificialus')).toBeInTheDocument();
  });

  it('offers create rather than minting a clade on submit', async () => {
    // app/Fish.md — explicit create over implicit create
    render(<FishEntry />);
    await userEvent.type(screen.getByLabelText('Clade'), 'Novus');
    const create = await screen.findByRole('button', { name: /create/ });
    await userEvent.click(create);
    // a level is asked for before anything is created, and the walk starts from there
    expect(screen.getByLabelText('level')).toBeInTheDocument();
    expect(api.postCharacter).not.toHaveBeenCalled();
  });

  it('walks upward and stops at the first ancestor already known', async () => {
    // app/Fish.md — the walk
    render(<FishEntry />);
    await userEvent.type(screen.getByLabelText('Clade'), 'Artificialus novus');
    await userEvent.click(await screen.findByRole('button', { name: /create/ }));
    await userEvent.click(screen.getByRole('button', { name: 'Start the walk' }));

    // the walk asks for the genus first — one level above species
    expect(screen.getByLabelText('genus')).toBeInTheDocument();
    api.searchClades.mockResolvedValue([
      { name: 'Artificialus', common_name: null, level: 'genus' },
    ]);
    await userEvent.type(screen.getByLabelText('genus'), 'Artific');
    await userEvent.click(await screen.findByRole('button', { name: 'Artificialus' }));

    // it stopped: nothing broader is asked for
    expect(screen.queryByLabelText('family')).not.toBeInTheDocument();
    expect(screen.getByText('parent')).toBeInTheDocument();
  });

  it('keeps the clade and the source after a submit and clears only the payload', async () => {
    // app/Fish.md — sticky fields with a cleared payload
    api.searchClades.mockResolvedValue([
      { name: claudus.name, common_name: claudus.common_name, level: 'species' },
    ]);
    api.searchSources.mockResolvedValue([brown]);
    api.postCharacter.mockResolvedValue({ clade: claudus.name, source: 17, char_id: 88 });

    render(<FishEntry />);
    await userEvent.type(screen.getByLabelText('Clade'), 'claud');
    await userEvent.click(await screen.findByRole('button', { name: /Artificialus claudus/ }));
    await userEvent.type(await screen.findByLabelText('Source'), 'bro');
    await userEvent.click(await screen.findByRole('button', { name: 'Brown, 2014' }));
    await userEvent.type(screen.getByLabelText('Character'), 'three dorsal spines');
    await userEvent.click(screen.getByRole('button', { name: 'Submit' }));

    await waitFor(() => {
      expect(api.postCharacter).toHaveBeenCalledWith({
        clade: 'Artificialus claudus',
        source: 17,
        text: 'three dorsal spines',
      });
    });
    expect(await screen.findByText('Saved.')).toBeInTheDocument();
    expect(screen.getByLabelText('Character')).toHaveValue('');
    expect(screen.getByText('Artificialus claudus')).toBeInTheDocument();
    expect(screen.getByText('Brown, 2014')).toBeInTheDocument();
  });
});
