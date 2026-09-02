// design/standards/Tests.md — Submit is disabled until every slot is filled, and Move on asks
// before it acts. The API is stubbed; what is under test is the screen's behaviour.

import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { beforeEach, describe, expect, it, vi } from 'vitest';

import type { Board, KinState } from '../api/types';
import { KinScreen } from './KinScreen';

const board: Board = {
  board_id: 7,
  level: 'species',
  ended: false,
  scored: false,
  clades: [
    { name: 'Artificialus claudus', common_name: 'spotted claudfish' },
    { name: 'Artificialus opus', common_name: null },
  ],
  citations: [{ src: 17, label: 'Brown, 2014' }],
  labels: { 17: 'Brown, 2014', 22: 'Okafor, 2021' },
  cards: [
    {
      kind: 'character',
      img_id: null,
      text: 'three dorsal spines',
      clade: { slot: 'cc-7', state: 'due', value: null },
      src: { slot: 'cs-88', state: 'due', value: null },
    },
    {
      kind: 'character',
      img_id: null,
      text: 'black caudal blotch',
      clade: { slot: 'cc-9', state: 'locked', value: 'Artificialus opus' },
      src: { slot: 'cs-90', state: 'locked', value: 22 },
    },
  ],
};

const state: KinState = {
  generated_on: new Date().toISOString().slice(0, 10),
  anchors_total: 4,
  anchors_left: 2,
  open_board: true,
};

const api = {
  kinState: vi.fn(),
  openBoard: vi.fn(),
  dealBoard: vi.fn(),
  generateSet: vi.fn(),
  submitBoard: vi.fn(),
  moveOn: vi.fn(),
  imageUrl: (id: string) => `/api/fish/images/${id}`,
};

vi.mock('../api/client', () => ({
  api: new Proxy({}, { get: (_, key: string) => api[key as keyof typeof api] }),
}));

beforeEach(() => {
  vi.clearAllMocks();
  api.kinState.mockResolvedValue(state);
  api.openBoard.mockResolvedValue(board);
});

function nth(elements: HTMLElement[], index: number): HTMLElement {
  const element = elements[index];
  if (!element) throw new Error(`no element at ${index}`);
  return element;
}

async function open() {
  render(<KinScreen />);
  await screen.findByText('three dorsal spines');
}

describe('the Kin board', () => {
  it('disables Submit until every blank is filled', async () => {
    // games/Kin.md — a complete board is required to submit
    await open();
    const submit = screen.getByRole('button', { name: 'Submit' });
    expect(submit).toBeDisabled();

    await userEvent.click(screen.getByRole('button', { name: /Artificialus claudus/ }));
    const cladeSlot = nth(screen.getAllByRole('button', { name: 'clade slot' }), 0);
    await userEvent.click(cladeSlot);
    expect(submit).toBeDisabled();

    await userEvent.click(screen.getByRole('button', { name: 'Brown, 2014' }));
    const srcSlot = nth(screen.getAllByRole('button', { name: 'source slot' }), 0);
    await userEvent.click(srcSlot);
    expect(submit).toBeEnabled();
  });

  it('fills a slot by tapping a chip then the slot, and clears it by tapping again', async () => {
    // app/Kin.md — tap-then-tap, and tapping a filled slot clears it
    await open();
    await userEvent.click(screen.getByRole('button', { name: /Artificialus claudus/ }));
    const cladeSlot = nth(screen.getAllByRole('button', { name: 'clade slot' }), 0);
    await userEvent.click(cladeSlot);
    expect(cladeSlot).toHaveTextContent('Artificialus claudus');
    await userEvent.click(cladeSlot);
    expect(cladeSlot).not.toHaveTextContent('Artificialus claudus');
  });

  it('never shows the answer to a live slot', async () => {
    // api/Kin.md
    await open();
    const slots = screen.getAllByRole('button', { name: 'clade slot' });
    const live = nth(slots, 0);
    const prefilled = nth(slots, 1);
    expect(live).toHaveTextContent('');
    // the prefilled card next to it does show its value
    expect(prefilled).toHaveTextContent('Artificialus opus');
  });

  it('asks before Move on acts', async () => {
    // app/Kin.md — it can fail a whole board in one tap
    await open();
    await userEvent.click(screen.getByRole('button', { name: 'Move on' }));
    expect(api.moveOn).not.toHaveBeenCalled();
    expect(screen.getByRole('dialog', { name: /Give up/ })).toBeInTheDocument();

    await userEvent.click(screen.getByRole('button', { name: 'Keep playing' }));
    expect(api.moveOn).not.toHaveBeenCalled();

    api.moveOn.mockResolvedValue({ ...board, ended: true, scored: true });
    await userEvent.click(screen.getByRole('button', { name: 'Move on' }));
    await userEvent.click(nth(screen.getAllByRole('button', { name: 'Move on' }), 1));
    await waitFor(() => {
      expect(api.moveOn).toHaveBeenCalledOnce();
    });
  });

  it('never offers Generate while a board is open', async () => {
    // app/Kin.md — drawing over it would discard a board the player is in the middle of
    api.kinState.mockResolvedValue({
      generated_on: '2020-01-01',
      anchors_total: 4,
      anchors_left: 0,
      open_board: true,
    });
    await open();
    expect(screen.queryByRole('button', { name: /Generate/ })).not.toBeInTheDocument();
    expect(screen.getByRole('button', { name: 'Submit' })).toBeInTheDocument();
  });

  it('offers Generate when the day has no set', async () => {
    // app/Kin.md — an explicit Generate over generating on open
    api.kinState.mockResolvedValue({
      generated_on: null,
      anchors_total: 0,
      anchors_left: 0,
      open_board: false,
    });
    api.openBoard.mockResolvedValue(null);
    render(<KinScreen />);
    expect(await screen.findByRole('button', { name: /Generate/ })).toBeInTheDocument();
  });

  it('offers a group size between boards rather than once a day', async () => {
    // app/Kin.md
    api.kinState.mockResolvedValue({ ...state, open_board: false });
    api.openBoard.mockResolvedValue(null);
    render(<KinScreen />);
    expect(await screen.findByLabelText('group size')).toBeInTheDocument();
    expect(screen.getByRole('button', { name: 'Start' })).toBeInTheDocument();
  });
});
