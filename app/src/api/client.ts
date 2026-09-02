// Every call the app makes. The endpoints are design/api/Fish.md and design/api/Kin.md.
// One origin, so every path is relative and there is no CORS.

import type {
  Board,
  CharacterCreated,
  CharacterEntry,
  CladeDetail,
  CladeResult,
  ImageCreated,
  KinState,
  Level,
  NewClade,
  NewSource,
  SourceResult,
  SubmitResponse,
} from './types';

export class ApiError extends Error {
  constructor(
    readonly status: number,
    message: string,
  ) {
    super(message);
    this.name = 'ApiError';
  }
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(path, init);
  if (!response.ok) {
    throw new ApiError(response.status, `${init?.method ?? 'GET'} ${path} → ${response.status}`);
  }
  return (await response.json()) as T;
}

export const api = {
  // ── the knowledge graph
  searchClades(q: string, level?: Level): Promise<CladeResult[]> {
    const params = new URLSearchParams({ q });
    if (level) params.set('level', level);
    return request<CladeResult[]>(`/api/fish/clades?${params.toString()}`);
  },

  /** A `404` is the walk's signal that the clade is new — see design/app/Fish.md. */
  async getClade(name: string): Promise<CladeDetail | null> {
    try {
      return await request<CladeDetail>(`/api/fish/clades/${encodeURIComponent(name)}`);
    } catch (error) {
      if (error instanceof ApiError && error.status === 404) return null;
      throw error;
    }
  },

  searchSources(q: string): Promise<SourceResult[]> {
    return request<SourceResult[]>(`/api/fish/sources?q=${encodeURIComponent(q)}`);
  },

  postCharacter(entry: CharacterEntry): Promise<CharacterCreated> {
    return request<CharacterCreated>('/api/fish/characters', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(entry),
    });
  },

  postImage(
    clade: string | NewClade,
    source: number | NewSource,
    image: File,
  ): Promise<ImageCreated> {
    const form = new FormData();
    form.set('json', JSON.stringify({ clade, source }));
    form.set('image', image);
    return request<ImageCreated>('/api/fish/images', { method: 'POST', body: form });
  },

  imageUrl(imgId: string): string {
    return `/api/fish/images/${encodeURIComponent(imgId)}`;
  },

  // ── playing Kin
  kinState(): Promise<KinState> {
    return request<KinState>('/api/kin/state');
  },

  generateSet(): Promise<KinState> {
    return request<KinState>('/api/kin/set', { method: 'POST' });
  },

  dealBoard(size: number): Promise<Board> {
    return request<Board>('/api/kin/board', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ size }),
    });
  },

  /** The open board, or null when there is none. */
  async openBoard(): Promise<Board | null> {
    try {
      return await request<Board>('/api/kin/board');
    } catch (error) {
      if (error instanceof ApiError && error.status === 404) return null;
      throw error;
    }
  },

  submitBoard(slots: Record<string, string | number>): Promise<SubmitResponse> {
    return request<SubmitResponse>('/api/kin/board/submit', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ slots }),
    });
  },

  moveOn(): Promise<Board> {
    return request<Board>('/api/kin/board/move-on', { method: 'POST' });
  },
};
