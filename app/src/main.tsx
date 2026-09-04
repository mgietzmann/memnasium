import { StrictMode } from 'react';
import { createRoot } from 'react-dom/client';
import { MathJaxContext } from 'better-react-mathjax';
import { App } from './App';
import './styles.css';

const config = {
  tex: { inlineMath: [['$', '$']], displayMath: [['$$', '$$']] },
};

createRoot(document.getElementById('root')!).render(
  <StrictMode>
    <MathJaxContext config={config}>
      <App />
    </MathJaxContext>
  </StrictMode>,
);
