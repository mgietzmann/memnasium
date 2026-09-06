import { useState } from 'react';
import { Home } from './screens/Home';
import { Entry } from './screens/Entry';
import { Drill } from './screens/Drill';
import { choose, ground, type Ground } from './theme';

/** Three screens, no deeper. Every screen carries a `← Home`. */
export type Screen = 'home' | 'entry' | 'drill';

export function App() {
  const [screen, setScreen] = useState<Screen>('home');
  if (screen === 'entry') return <Entry onHome={() => setScreen('home')} />;
  if (screen === 'drill') return <Drill onHome={() => setScreen('home')} />;
  return <Home onGo={setScreen} />;
}

/**
 * The same on all three screens: `← Home` on the left — `memnasium` on Home
 * itself, which has nowhere to go back to — the screen's name on the right, and
 * the toggle beyond it. See design/app/Home.md#navigation.
 */
export function TopBar({ title, onHome }: { title: string; onHome?: () => void }) {
  return (
    <div className="topbar">
      {onHome ? (
        <button className="link" onClick={onHome}>
          ← Home
        </button>
      ) : (
        <h1>memnasium</h1>
      )}
      <span className="right">
        <span className="label">{title}</span>
        <ThemeToggle />
      </span>
    </div>
  );
}

/**
 * One control showing the ground it will switch **to**. It belongs on every
 * screen rather than on Home alone — the ground is wrong at the moment it is
 * noticed, which is usually mid-board.
 */
function ThemeToggle() {
  const [current, setCurrent] = useState<Ground>(ground);
  const next: Ground = current === 'dark' ? 'light' : 'dark';
  return (
    <button
      className="theme"
      aria-label={`switch to ${next}`}
      onClick={() => {
        choose(next);
        setCurrent(next);
      }}
    >
      {next === 'light' ? '☀' : '☾'}
    </button>
  );
}
