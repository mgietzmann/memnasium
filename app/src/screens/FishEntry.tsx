// The half of memnasium where facts go in — design/app/Fish.md.
// Two tabs over one form; they differ only in the payload band. Everything but the payload
// sticks after a submit, because the slow part of entry is the clade and the source.

import { useCallback, useEffect, useRef, useState } from 'react';

import { api } from '../api/client';
import type {
  Ancestor,
  CladeDetail,
  CladeResult,
  Level,
  NewAncestor,
  NewClade,
  SourceResult,
} from '../api/types';
import { LEVELS } from '../api/types';
import { Button } from '../components/Button';
import { SearchField } from '../components/SearchField';
import { Tabs } from '../components/Tabs';

const TABS = ['Images', 'Characters'] as const;
type Tab = (typeof TABS)[number];

/** A clade being created, and how far the walk has climbed towards a known ancestor. */
interface Walk {
  name: string;
  commonName: string;
  level: Level;
  /** Index into LEVELS of the level being asked for, or -1 once the walk has run out. */
  asking: number;
  newAncestors: NewAncestor[];
  parent: string | null;
  done: boolean;
}

function startWalk(name: string, level: Level): Walk {
  const asking = LEVELS.indexOf(level) - 1;
  return {
    name,
    commonName: '',
    level,
    asking,
    newAncestors: [],
    parent: null,
    done: asking < 0,
  };
}

/** Move one level broader. Running out of levels leaves the new clade a root. */
function climb(walk: Walk, ancestor?: NewAncestor): Walk {
  const asking = walk.asking - 1;
  return {
    ...walk,
    asking,
    newAncestors: ancestor ? [...walk.newAncestors, ancestor] : walk.newAncestors,
    done: asking < 0,
  };
}

function toNewClade(walk: Walk): NewClade {
  return {
    name: walk.name,
    common_name: walk.commonName.trim() === '' ? null : walk.commonName.trim(),
    level: walk.level,
    new_ancestors: walk.newAncestors,
    parent: walk.parent,
  };
}

export function FishEntry() {
  const [tab, setTab] = useState<Tab>('Characters');

  // ── the clade block
  const [cladeQuery, setCladeQuery] = useState('');
  const [picked, setPicked] = useState<CladeDetail | null>(null);
  const [walk, setWalk] = useState<Walk | null>(null);
  const [newLevel, setNewLevel] = useState<Level>('species');
  const [pendingName, setPendingName] = useState<string | null>(null);
  const [ancestorQuery, setAncestorQuery] = useState('');

  // ── the source block
  const [sourceQuery, setSourceQuery] = useState('');
  const [source, setSource] = useState<SourceResult | null>(null);
  const [newSource, setNewSource] = useState<{
    author: string;
    year: string;
    title: string;
  } | null>(null);

  // ── the payload
  const [text, setText] = useState('');
  const [file, setFile] = useState<File | null>(null);
  const [message, setMessage] = useState('');
  const fileInput = useRef<HTMLInputElement>(null);

  const searchClades = useCallback((q: string) => api.searchClades(q), []);
  const searchSources = useCallback((q: string) => api.searchSources(q), []);
  const askingLevel: Level | null = walk && walk.asking >= 0 ? (LEVELS[walk.asking] ?? null) : null;
  const searchAncestors = useCallback(
    (q: string) => api.searchClades(q, askingLevel ?? undefined),
    [askingLevel],
  );

  useEffect(() => {
    setAncestorQuery('');
  }, [walk?.asking]);

  const cladeReady = picked !== null || (walk !== null && walk.done);
  const sourceReady =
    source !== null ||
    (newSource !== null && newSource.author.trim() !== '' && newSource.year.trim() !== '');
  const payloadReady = tab === 'Characters' ? text.trim() !== '' : file !== null;

  function resetClade() {
    setPicked(null);
    setWalk(null);
    setPendingName(null);
    setCladeQuery('');
  }

  async function submit() {
    const cladeRef = picked ? picked.name : walk ? toNewClade(walk) : null;
    if (!cladeRef) return;
    const sourceRef = source
      ? source.src
      : newSource
        ? {
            author: newSource.author.trim(),
            year: Number(newSource.year),
            title: newSource.title.trim(),
          }
        : null;
    if (sourceRef === null) return;

    try {
      const created =
        tab === 'Characters'
          ? await api.postCharacter({ clade: cladeRef, source: sourceRef, text: text.trim() })
          : file
            ? await api.postImage(cladeRef, sourceRef, file)
            : null;
      if (!created) return;

      // The response is what the next submission should send, so the sticky form stops creating.
      const detail = await api.getClade(created.clade);
      setPicked(detail);
      setWalk(null);
      setPendingName(null);
      const sources = await api.searchSources(String(created.source));
      setSource(sources.find((s) => s.src === created.source) ?? source);
      setNewSource(null);
      setText('');
      setFile(null);
      if (fileInput.current) fileInput.current.value = '';
      setMessage('Saved.');
    } catch (error) {
      setMessage(error instanceof Error ? error.message : 'Failed.');
    }
  }

  return (
    <div className="entry">
      <h1>Data entry</h1>
      <Tabs tabs={TABS} active={tab} onChange={setTab} />

      <section className="band">
        {picked === null && walk === null && pendingName === null && (
          <SearchField<CladeResult>
            label="Clade"
            query={cladeQuery}
            onQueryChange={setCladeQuery}
            search={searchClades}
            optionKey={(row) => row.name}
            renderOption={(row) => (
              <>
                <span className="sci">{row.name}</span> <span className="label">{row.level}</span>
              </>
            )}
            onPick={(row) => {
              void api.getClade(row.name).then(setPicked);
              setCladeQuery('');
            }}
            onCreate={setPendingName}
          />
        )}

        {pendingName !== null && (
          <div className="field">
            <span className="label">New clade</span>
            <div className="row">
              <span className="sci">{pendingName}</span>
              <select
                className="input input-inline"
                aria-label="level"
                value={newLevel}
                onChange={(event) => {
                  setNewLevel(event.target.value as Level);
                }}
              >
                {LEVELS.map((level) => (
                  <option key={level} value={level}>
                    {level}
                  </option>
                ))}
              </select>
              <Button
                onClick={() => {
                  setWalk(startWalk(pendingName, newLevel));
                  setPendingName(null);
                }}
              >
                Start the walk
              </Button>
              <button type="button" className="link" onClick={resetClade}>
                cancel
              </button>
            </div>
          </div>
        )}

        {picked !== null && (
          <div className="field">
            <span className="label">Clade</span>
            <div className="field-picked">
              <span className="sci">{picked.name}</span>
              {picked.common_name && <span className="common">{picked.common_name}</span>}
              <span className="label">{picked.level}</span>
              <span className="known">✓ known</span>
              <button type="button" className="link" onClick={resetClade}>
                change
              </button>
            </div>
            <ChainRows ancestors={picked.ancestors} />
          </div>
        )}

        {walk !== null && (
          <div className="field">
            <span className="label">New clade</span>
            <div className="field-picked">
              <span className="sci">{walk.name}</span>
              <span className="label">{walk.level}</span>
              <button type="button" className="link" onClick={resetClade}>
                cancel
              </button>
            </div>
            <input
              className="input"
              placeholder="common name (optional)"
              aria-label="common name"
              value={walk.commonName}
              onChange={(event) => {
                setWalk({ ...walk, commonName: event.target.value });
              }}
            />
            <ChainRows
              ancestors={[...walk.newAncestors].map((a) => ({ name: a.name, level: a.level }))}
              parent={walk.parent}
            />
            {!walk.done && askingLevel !== null && (
              <div className="walk-step">
                <SearchField<CladeResult>
                  label={askingLevel}
                  query={ancestorQuery}
                  onQueryChange={setAncestorQuery}
                  search={searchAncestors}
                  optionKey={(row) => row.name}
                  renderOption={(row) => <span className="sci">{row.name}</span>}
                  onPick={(row) => {
                    // The walk stops at the first level whose answer already exists.
                    setWalk({ ...walk, parent: row.name, done: true, asking: -1 });
                  }}
                  onCreate={(name) => {
                    setWalk(climb(walk, { name, level: askingLevel }));
                  }}
                />
                <div className="row">
                  <button
                    type="button"
                    className="link"
                    onClick={() => {
                      setWalk(climb(walk));
                    }}
                  >
                    skip {askingLevel}
                  </button>
                  <button
                    type="button"
                    className="link"
                    onClick={() => {
                      setWalk({ ...walk, done: true, asking: -1, parent: null });
                    }}
                  >
                    no parent — it is a root
                  </button>
                </div>
              </div>
            )}
          </div>
        )}
      </section>

      <section className="band">
        {source === null && newSource === null && (
          <SearchField<SourceResult>
            label="Source"
            query={sourceQuery}
            onQueryChange={setSourceQuery}
            search={searchSources}
            optionKey={(row) => String(row.src)}
            renderOption={(row) => <span className="cite">{row.label}</span>}
            onPick={(row) => {
              setSource(row);
              setSourceQuery('');
            }}
            onCreate={(q) => {
              setNewSource({ author: q, year: '', title: '' });
            }}
          />
        )}
        {source !== null && (
          <div className="field">
            <span className="label">Source</span>
            <div className="field-picked">
              <span className="cite">{source.label}</span>
              <span className="known">✓ known</span>
              <button
                type="button"
                className="link"
                onClick={() => {
                  setSource(null);
                  setSourceQuery('');
                }}
              >
                change
              </button>
            </div>
          </div>
        )}
        {newSource !== null && (
          <div className="field">
            <span className="label">New source</span>
            <div className="row">
              <input
                className="input"
                aria-label="author"
                placeholder="author"
                value={newSource.author}
                onChange={(event) => {
                  setNewSource({ ...newSource, author: event.target.value });
                }}
              />
              <input
                className="input input-inline"
                aria-label="year"
                placeholder="year"
                inputMode="numeric"
                value={newSource.year}
                onChange={(event) => {
                  setNewSource({ ...newSource, year: event.target.value });
                }}
              />
              <input
                className="input"
                aria-label="title"
                placeholder="title"
                value={newSource.title}
                onChange={(event) => {
                  setNewSource({ ...newSource, title: event.target.value });
                }}
              />
              <button
                type="button"
                className="link"
                onClick={() => {
                  setNewSource(null);
                }}
              >
                cancel
              </button>
            </div>
          </div>
        )}
      </section>

      <section className="band">
        {tab === 'Characters' ? (
          <div className="field">
            <label className="label" htmlFor="character-text">
              Character
            </label>
            <input
              id="character-text"
              className="input"
              value={text}
              onChange={(event) => {
                setText(event.target.value);
              }}
            />
          </div>
        ) : (
          <div className="field">
            <label className="label" htmlFor="image-file">
              Image
            </label>
            <input
              id="image-file"
              className="input"
              type="file"
              accept="image/*"
              ref={fileInput}
              onChange={(event) => {
                setFile(event.target.files?.[0] ?? null);
              }}
            />
          </div>
        )}
      </section>

      <div className="row row-end">
        {message && <span className="common">{message}</span>}
        <Button
          disabled={!cladeReady || !sourceReady || !payloadReady}
          onClick={() => {
            void submit();
          }}
        >
          Submit
        </Button>
      </div>
    </div>
  );
}

function ChainRows({ ancestors, parent }: { ancestors: Ancestor[]; parent?: string | null }) {
  if (ancestors.length === 0 && !parent) return null;
  return (
    <div className="chain">
      {ancestors.map((ancestor) => (
        <div key={ancestor.name} className="chain-row">
          <span className="label">{ancestor.level}</span>
          <span className="sci">{ancestor.name}</span>
        </div>
      ))}
      {parent && (
        <div className="chain-row">
          <span className="label">parent</span>
          <span className="sci">{parent}</span>
          <span className="known">✓ known</span>
        </div>
      )}
    </div>
  );
}
