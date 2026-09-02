// design/standards/Tests.md — a Slot moves empty → filled → locked and refuses interaction
// when locked. Queried by what the player sees, never by class name.

import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { describe, expect, it, vi } from 'vitest';

import { Slot } from './Slot';

describe('Slot', () => {
  it('shows nothing when empty and calls back when tapped', async () => {
    // app/Components.md
    const onClick = vi.fn();
    render(<Slot kind="clade" state="empty" onClick={onClick} />);
    const slot = screen.getByRole('button', { name: 'clade slot' });
    expect(slot).toHaveTextContent('');
    await userEvent.click(slot);
    expect(onClick).toHaveBeenCalledOnce();
  });

  it('shows its value when filled and can be tapped to clear it', async () => {
    // app/Components.md
    const onClick = vi.fn();
    render(<Slot kind="clade" state="filled" value="Artificialus opus" onClick={onClick} />);
    await userEvent.click(screen.getByRole('button', { name: 'clade slot' }));
    expect(screen.getByText('Artificialus opus')).toBeInTheDocument();
    expect(onClick).toHaveBeenCalledOnce();
  });

  it('refuses interaction when locked', async () => {
    // app/Components.md
    const onClick = vi.fn();
    render(<Slot kind="source" state="locked" value="Brown, 2014" onClick={onClick} />);
    const slot = screen.getByRole('button', { name: 'source slot' });
    expect(slot).toBeDisabled();
    await userEvent.click(slot);
    expect(onClick).not.toHaveBeenCalled();
  });

  it('marks a locked slot with a glyph, so hue is never what tells the states apart', () => {
    // standards/Style.md
    render(<Slot kind="clade" state="locked" value="Artificialus opus" />);
    expect(screen.getByRole('button', { name: 'clade slot' })).toHaveTextContent('✓');
  });
});
