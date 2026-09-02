// Every payload's shape, taken from the OpenAPI schema the Pydantic models produce.
// Nothing here is hand-written — a field renamed in Python breaks this build, which is the point.
// See design/standards/Code.md.

import type { components } from './schema';

type S = components['schemas'];

export type Level = S['Level'];
export type CladeResult = S['CladeResult'];
export type CladeDetail = S['CladeDetail'];
export type Ancestor = S['Ancestor'];
export type SourceResult = S['SourceResult'];
export type NewClade = S['NewClade'];
export type NewAncestor = S['NewAncestor'];
export type NewSource = S['NewSource'];
export type CharacterEntry = S['CharacterEntry'];
export type CharacterCreated = S['CharacterCreated'];
export type ImageCreated = S['ImageCreated'];

export type KinState = S['KinState'];
export type Board = S['Board'];
export type Card = S['Card'];
export type Slot = S['Slot'];
export type PaletteClade = S['PaletteClade'];
export type Citation = S['Citation'];
export type SubmitResponse = S['SubmitResponse'];

export const LEVELS: Level[] = [
  'class',
  'order',
  'suborder',
  'family',
  'subfamily',
  'genus',
  'species',
];
