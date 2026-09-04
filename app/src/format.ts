/**
 * How numbers are printed. Nothing here computes anything — both the corpus and
 * the expectation arrive from `GET /home` — see design/app/Home.md.
 */

/** The live corpus, as the screens print it: `1,204 pairs`. */
export function pairs(n: number): string {
  return `${n.toLocaleString('en-US')} pairs`;
}

/**
 * The expectation, always with a `~`. The draw is a coin flip per pair, so its
 * size is a random variable and its mean is not a count — a bare number beside
 * `118 drawn` would read as a promise the maths never made.
 */
export function expected(n: number): string {
  return `~${Math.round(n).toLocaleString('en-US')} expected`;
}
