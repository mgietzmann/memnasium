import { beforeEach, describe, expect, it, vi } from 'vitest';
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { TopBar } from '../App';
import { apply, ground } from '../theme';

/** Which ground the app is read on — design/standards/Style.md#choosing-a-theme. */

function prefersLight(matches: boolean) {
  vi.spyOn(window, 'matchMedia').mockImplementation(
    (query: string) => ({ matches, media: query }) as MediaQueryList,
  );
}

beforeEach(() => {
  localStorage.clear();
  document.documentElement.removeAttribute('data-theme');
  vi.restoreAllMocks();
});

describe('choosing a theme', () => {
  it('falls back to dark when the OS states no preference', () => {
    prefersLight(false);
    expect(ground()).toBe('dark');
    apply();
    expect(document.documentElement.hasAttribute('data-theme')).toBe(false);
  });

  it('honours an OS asking for light, while the toggle is untouched', () => {
    prefersLight(true);
    expect(ground()).toBe('light');
    apply();
    // Nothing is stamped: the media query is what decides, not the attribute.
    expect(document.documentElement.hasAttribute('data-theme')).toBe(false);
  });

  it('lets a choice override the OS in both directions', async () => {
    // Or the toggle could only ever move a viewer away from what the OS said
    const user = userEvent.setup();
    prefersLight(true);
    render(<TopBar title="Drill" onHome={vi.fn()} />);

    // Light on screen, so the control offers dark.
    await user.click(screen.getByRole('button', { name: 'switch to dark' }));
    expect(document.documentElement.getAttribute('data-theme')).toBe('dark');
    expect(ground()).toBe('dark');

    await user.click(screen.getByRole('button', { name: 'switch to light' }));
    expect(document.documentElement.getAttribute('data-theme')).toBe('light');
    expect(ground()).toBe('light');
  });

  it('survives a reload, per browser', () => {
    prefersLight(false);
    localStorage.setItem('memnasium.theme', 'light');
    apply();
    expect(document.documentElement.getAttribute('data-theme')).toBe('light');
    expect(ground()).toBe('light');
  });

  it('shows the ground it will switch to, on every screen', () => {
    // app/Home.md#navigation — `☀` while dark, `☾` while light
    prefersLight(false);
    render(<TopBar title="Entry" onHome={vi.fn()} />);
    expect(screen.getByRole('button', { name: 'switch to light' })).toHaveTextContent('☀');
  });
});
