// design/standards/Tests.md — a Chip stays selectable after being used. Nothing is consumed,
// so the board cannot be solved by elimination (design/app/Kin.md).

import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { describe, expect, it, vi } from 'vitest';

import { Chip } from './Chip';

describe('Chip', () => {
  it('stays selectable after being used', async () => {
    // app/Kin.md — nothing is consumed
    const onClick = vi.fn();
    render(<Chip onClick={onClick}>Brown, 2014</Chip>);
    const chip = screen.getByRole('button', { name: 'Brown, 2014' });
    await userEvent.click(chip);
    await userEvent.click(chip);
    expect(onClick).toHaveBeenCalledTimes(2);
    expect(screen.getByRole('button', { name: 'Brown, 2014' })).toBeInTheDocument();
  });

  it('reports whether it is selected', () => {
    // app/Components.md
    render(<Chip selected>Brown, 2014</Chip>);
    expect(screen.getByRole('button', { name: 'Brown, 2014' })).toHaveAttribute(
      'aria-pressed',
      'true',
    );
  });
});
