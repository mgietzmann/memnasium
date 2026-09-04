import { describe, expect, it, vi } from 'vitest';
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { Board } from '../components/Board';
import { api } from '../api/client';

vi.mock('better-react-mathjax', () => ({
  MathJax: ({ children }: { children: React.ReactNode }) => <span>{children}</span>,
  MathJaxContext: ({ children }: { children: React.ReactNode }) => <>{children}</>,
}));

const due = [
  { id: 1, question: 'Puget Sound, inshore?' },
  { id: 2, question: 'Puget Sound, offshore?' },
];

const context = [
  {
    id: 3,
    question: 'Yukon, freshwater?',
    answer: '85-90 mm',
    source: { id: 1, author: 'Bradford', year: 2009, publication: null },
  },
];

function board(overrides: Partial<Parameters<typeof Board>[0]> = {}) {
  return render(
    <Board
      title="Onset of piscivory"
      pairCount={3}
      position="board 1 of 1"
      due={due}
      context={context}
      onConfirmed={vi.fn()}
      {...overrides}
    />,
  );
}

describe('a board', () => {
  it('disables Submit until every box has something in it', async () => {
    // standards/Tests.md#the-app
    const user = userEvent.setup();
    board();
    const submit = screen.getByRole('button', { name: 'Submit' });
    expect(submit).toBeDisabled();
    await user.type(screen.getByLabelText('answer for pair 1'), '70 mm');
    await user.type(screen.getByLabelText('source for pair 1'), 'Duffy 2010');
    expect(submit).toBeDisabled();
    await user.type(screen.getByLabelText('answer for pair 2'), '130 mm');
    await user.type(screen.getByLabelText('source for pair 2'), 'Duffy 2010');
    expect(submit).toBeEnabled();
  });

  it('renders a context pair with its answer and offers no input', () => {
    board();
    expect(screen.getByText('85-90 mm')).toBeInTheDocument();
    expect(screen.getByText('Bradford 2009')).toBeInTheDocument();
    expect(screen.queryByLabelText('answer for pair 3')).not.toBeInTheDocument();
  });

  it('renders a roll batch with no context column', () => {
    // app/Drilling.md#a-roll-batch
    board({ context: [], title: 'The roll' });
    expect(screen.queryByText('85-90 mm')).not.toBeInTheDocument();
  });

  it('passes LaTeX through unmangled', () => {
    // standards/Tests.md#what-is-not-tested — the library renders; we check delivery
    board({ due: [{ id: 1, question: 'At $70$ mm?' }] });
    expect(screen.getByText('At $70$ mm?')).toBeInTheDocument();
  });

  it('lets a missed pair be contested, and the contest survives to Confirm', async () => {
    // flows/Drilling.md#contest-and-confirm
    const user = userEvent.setup();
    vi.spyOn(api, 'grade').mockResolvedValue({
      verdicts: [
        {
          recall_pair_id: 1,
          answer_correct: false,
          source_correct: true,
          right_answer: '70 mm',
          right_source: null,
        },
        {
          recall_pair_id: 2,
          answer_correct: true,
          source_correct: true,
          right_answer: null,
          right_source: null,
        },
      ],
    });
    const confirm = vi.spyOn(api, 'confirm').mockResolvedValue(undefined);
    board();
    for (const id of [1, 2]) {
      await user.type(screen.getByLabelText(`answer for pair ${id}`), 'x');
      await user.type(screen.getByLabelText(`source for pair ${id}`), 'y');
    }
    await user.click(screen.getByRole('button', { name: 'Submit' }));
    expect(await screen.findByText('70 mm')).toBeInTheDocument();

    await user.click(screen.getByRole('button', { name: 'contest' }));
    expect(screen.queryByRole('button', { name: 'contest' })).not.toBeInTheDocument();

    await user.click(screen.getByRole('button', { name: 'Confirm' }));
    expect(confirm).toHaveBeenCalledWith([
      { recall_pair_id: 1, correct: true, user_answer: 'x', user_source: 'y' },
      { recall_pair_id: 2, correct: true, user_answer: 'x', user_source: 'y' },
    ]);
  });
});
