import { StrictMode } from 'react';
import { createRoot } from 'react-dom/client';
import { MathJaxContext } from 'better-react-mathjax';
import { App } from './App';
import { apply } from './theme';
import './styles.css';

const config = {
  tex: { inlineMath: [['$', '$']], displayMath: [['$$', '$$']] },
};

// The stored choice, back on the root before anything paints.
apply();

createRoot(document.getElementById('root')!).render(
  <StrictMode>
    <MathJaxContext config={config}>
      <App />
    </MathJaxContext>
  </StrictMode>,
);
