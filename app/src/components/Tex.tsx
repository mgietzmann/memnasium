import { MathJax } from 'better-react-mathjax';

/**
 * Renders a statement with its LaTeX intact.
 *
 * MathJax defaults to its own colour; a formula that is a different grey from
 * the sentence around it reads as a quotation — design/standards/Style.md.
 */
export function Tex({ children }: { children: string }) {
  return (
    <MathJax inline dynamic style={{ color: 'inherit', fontSize: 'inherit' }}>
      {children}
    </MathJax>
  );
}
