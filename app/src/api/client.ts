import type { components } from './schema';

/**
 * The one surface over the store, as the app sees it.
 *
 * Every type here is generated from the Pydantic models — see
 * design/standards/Code.md#one-definition-of-a-payload. Nothing is hand-written.
 */
type Schemas = components['schemas'];

export type Source = Schemas['Source'];
export type Note = Schemas['Note'];
export type Group = Schemas['Group'];
export type Home = Schemas['Home'];
export type DrawSummary = Schemas['DrawSummary'];
export type Board = Schemas['Board'];
export type RollBatch = Schemas['RollBatch'];
export type DuePair = Schemas['DuePair'];
export type ContextPair = Schemas['ContextPair'];
export type Verdict = Schemas['Verdict'];
export type Answer = Schemas['Answer'];
export type ConfirmResult = Schemas['ConfirmResult'];

/** A refusal from the store, carrying the reason it gave. */
export class ApiError extends Error {
  constructor(
    readonly status: number,
    readonly code: string,
    detail: string,
  ) {
    super(detail);
  }
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`/api${path}`, {
    headers: init?.body ? { 'Content-Type': 'application/json' } : undefined,
    ...init,
  });
  if (!response.ok) {
    const body: unknown = await response.json().catch(() => ({}));
    const shape = body as { code?: string; detail?: unknown };
    const detail =
      typeof shape.detail === 'string' ? shape.detail : `${response.status} on ${path}`;
    throw new ApiError(response.status, shape.code ?? 'error', detail);
  }
  if (response.status === 204) return undefined as T;
  return (await response.json()) as T;
}

const post = <T>(path: string, body?: unknown): Promise<T> =>
  request<T>(path, { method: 'POST', body: body === undefined ? undefined : JSON.stringify(body) });

export const api = {
  home: () => request<Home>('/home'),

  // The current draw is read through `/home`, which is the only route
  // carrying the corpus and the expectation beside it — design/api/API.md.
  buildDraw: () => post<DrawSummary>('/draw'),
  boards: (n: number) => request<Board[]>(`/draw/boards?n=${n}`),
  roll: (n: number) => request<RollBatch>(`/draw/roll?n=${n}`),
  grade: (answers: Answer[]) => post<{ verdicts: Verdict[] }>('/grade', { answers }),
  confirm: (results: ConfirmResult[]) => post<void>('/confirm', { results }),

  searchSources: (q: string) => request<Source[]>(`/sources?q=${encodeURIComponent(q)}`),
  createSource: (source: Schemas['SourceCreate']) => post<Source>('/sources', source),
  createNote: (note: Schemas['NoteCreate']) => post<Note>('/notes', note),
  editNote: (id: number, statement: string) =>
    request<Note>(`/notes/${id}`, { method: 'PATCH', body: JSON.stringify({ statement }) }),
  deleteNote: (id: number) => request<void>(`/notes/${id}`, { method: 'DELETE' }),
  notes: (id: number) => request<Note[]>(`/notes?q=&source_id=${id}`),

  groups: () => request<Group[]>('/groups'),
};
