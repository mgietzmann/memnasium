// design/app/Navigation.md — the games card's table, every row of it.

import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';

import type { KinState } from './api/types';
import { kinStateLine, needsGenerate } from './kinDay';

const today = () => new Date().toLocaleDateString('en-CA');

function state(
  generated_on: string | null,
  total: number,
  left: number,
  open_board = false,
): KinState {
  return { generated_on, anchors_total: total, anchors_left: left, open_board };
}

describe('the games card', () => {
  it('reads not generated when there is no set at all', () => {
    // app/Navigation.md
    expect(kinStateLine(state(null, 0, 0))).toBe('not generated');
    expect(needsGenerate(state(null, 0, 0))).toBe(true);
  });

  it('counts anchors resolved out of the set drawn today', () => {
    // app/Navigation.md
    expect(kinStateLine(state(today(), 12, 12))).toBe('0 / 12 anchors');
    expect(kinStateLine(state(today(), 12, 7))).toBe('5 / 12 anchors');
  });

  it('reads done for today once a set drawn today is spent', () => {
    // app/Navigation.md
    expect(kinStateLine(state(today(), 12, 0))).toBe('done for today');
    expect(needsGenerate(state(today(), 12, 0))).toBe(false);
  });

  it('carries an unfinished set over rather than asking for a new draw', () => {
    // app/Navigation.md
    expect(kinStateLine(state('2000-01-01', 12, 7))).toBe('5 / 12 anchors');
    expect(needsGenerate(state('2000-01-01', 12, 7))).toBe(false);
  });

  it('reads not generated once an older set is spent', () => {
    // app/Navigation.md
    expect(kinStateLine(state('2000-01-01', 12, 0))).toBe('not generated');
    expect(needsGenerate(state('2000-01-01', 12, 0))).toBe(true);
  });

  it('lets an open board outrank every other row', () => {
    // app/Navigation.md — a set with an open board is never spent
    expect(kinStateLine(state('2000-01-01', 12, 0, true))).toBe('board in progress');
    expect(kinStateLine(state(today(), 12, 0, true))).toBe('board in progress');
  });

  it('never offers Generate while a board is open', () => {
    // app/Kin.md — drawing over it would discard a board the player is in the middle of
    expect(needsGenerate(state('2000-01-01', 12, 0, true))).toBe(false);
  });
});

describe('the day boundary', () => {
  beforeEach(() => {
    vi.stubEnv('TZ', 'America/Los_Angeles');
    vi.useFakeTimers();
  });

  afterEach(() => {
    vi.useRealTimers();
    vi.unstubAllEnvs();
  });

  it('reads the day in local time, matching the server', () => {
    // app/Navigation.md — the server stamps generated_on with its own local date
    // 19:30 on 2 September in Los Angeles is already 3 September in UTC.
    vi.setSystemTime(new Date('2026-09-03T02:30:00Z'));
    expect(kinStateLine(state('2026-09-02', 12, 0))).toBe('done for today');
    expect(needsGenerate(state('2026-09-02', 12, 0))).toBe(false);
    expect(kinStateLine(state('2026-09-02', 12, 5))).toBe('7 / 12 anchors');
  });
});
