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

/**
 * A day written out, as Review's header line prints it: `8 September`.
 *
 * Parsed as a local date rather than through `new Date(iso)`, which reads a bare
 * ISO date as UTC and prints the day before it west of Greenwich.
 */
export function day(iso: string): string {
  const [year, month, date] = iso.split('-').map(Number);
  return new Date(year, month - 1, date).toLocaleDateString('en-GB', {
    day: 'numeric',
    month: 'long',
  });
}
