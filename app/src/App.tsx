import { useState } from 'react';
import { Home } from './screens/Home';
import { Entry } from './screens/Entry';
import { Drill } from './screens/Drill';

/** Three screens, no deeper. Every screen carries a `← Home`. */
export type Screen = 'home' | 'entry' | 'drill';

export function App() {
  const [screen, setScreen] = useState<Screen>('home');
  if (screen === 'entry') return <Entry onHome={() => setScreen('home')} />;
  if (screen === 'drill') return <Drill onHome={() => setScreen('home')} />;
  return <Home onGo={setScreen} />;
}

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
      <span className="label">{title}</span>
    </div>
  );
}
