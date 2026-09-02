// Two cards, nothing else — there are exactly two things to do, and persistent chrome would be
// chrome around nothing (design/app/Navigation.md).

import type { Screen } from '../App';

export interface HomeProps {
  onGo: (screen: Screen) => void;
}

export function Home({ onGo }: HomeProps) {
  return (
    <div className="home">
      <button
        type="button"
        className="home-card"
        onClick={() => {
          onGo('games');
        }}
      >
        <h2>Games</h2>
        <p className="common">play today’s sets</p>
      </button>
      <button
        type="button"
        className="home-card"
        onClick={() => {
          onGo('entry');
        }}
      >
        <h2>Entry</h2>
        <p className="common">add what you read</p>
      </button>
    </div>
  );
}
