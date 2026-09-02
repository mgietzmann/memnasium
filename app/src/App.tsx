// The whole map: Home leads to Games and to Fish entry, and Games leads to a game's screen
// (design/app/Navigation.md). Nothing is routed on a server, so a screen is a piece of state.

import { useState } from 'react';

import { FishEntry } from './screens/FishEntry';
import { Games } from './screens/Games';
import { Home } from './screens/Home';
import { KinScreen } from './screens/KinScreen';

export type Screen = 'home' | 'games' | 'kin' | 'entry';

export function App() {
  const [screen, setScreen] = useState<Screen>('home');

  return (
    <div className="app">
      <header className="app-bar">
        <button
          type="button"
          className="brand"
          onClick={() => {
            setScreen('home');
          }}
        >
          memnasium
        </button>
        {screen !== 'home' && (
          <button
            type="button"
            className="link"
            onClick={() => {
              setScreen(screen === 'kin' ? 'games' : 'home');
            }}
          >
            ← back
          </button>
        )}
      </header>
      <main className="app-main">
        {screen === 'home' && <Home onGo={setScreen} />}
        {screen === 'games' && (
          <Games
            onOpen={() => {
              setScreen('kin');
            }}
          />
        )}
        {screen === 'kin' && <KinScreen />}
        {screen === 'entry' && <FishEntry />}
      </main>
    </div>
  );
}
