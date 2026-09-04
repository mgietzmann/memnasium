import { useEffect, useState } from 'react';
import { api, type Note, type Source } from '../api/client';
import { TopBar } from '../App';
import { Tex } from '../components/Tex';

const label = (s: Source) => `${s.author} ${s.year}${s.publication ? ` — ${s.publication}` : ''}`;

/** Typing a note in against its source — design/app/Entry.md. */
export function Entry({ onHome }: { onHome: () => void }) {
  // The source is sticky: picked once and held across saves.
  const [source, setSource] = useState<Source | null>(null);
  const [query, setQuery] = useState('');
  const [found, setFound] = useState<Source[]>([]);
  const [statement, setStatement] = useState('');
  const [entered, setEntered] = useState<Note[]>([]);
  const [creating, setCreating] = useState(false);

  useEffect(() => {
    if (source || !query) {
      setFound([]);
      return;
    }
    let live = true;
    void api.searchSources(query).then((rows) => {
      if (live) setFound(rows);
    });
    return () => {
      live = false;
    };
  }, [query, source]);

  const save = () => {
    if (!source || !statement.trim()) return;
    void api.createNote({ source_id: source.id, statement }).then((note) => {
      setEntered((prior) => [note, ...prior]);
      setStatement('');
    });
  };

  return (
    <div className="screen">
      <TopBar title="Entry" onHome={onHome} />

      <div className="panel">
        <div className="label">Source</div>
        {source ? (
          <div>
            {label(source)}{' '}
            <button className="link" aria-label="clear source" onClick={() => setSource(null)}>
              ×
            </button>
          </div>
        ) : (
          <>
            <input
              placeholder="search sources…"
              aria-label="search sources"
              value={query}
              onChange={(e) => setQuery(e.target.value)}
            />
            {query && found.length > 0 && (
              <div className="results">
                {found.map((s) => (
                  <button key={s.id} onClick={() => setSource(s)}>
                    {label(s)}
                  </button>
                ))}
              </div>
            )}
            {query && found.length === 0 && !creating && (
              <p className="muted">
                Nothing matches.{' '}
                <button className="link" onClick={() => setCreating(true)}>
                  create this source
                </button>
              </p>
            )}
            {creating && (
              <CreateSource
                onCreated={(s) => {
                  setSource(s);
                  setCreating(false);
                  setQuery('');
                }}
              />
            )}
          </>
        )}
      </div>

      <div className="split">
        <div>
          <div className="label">Statement</div>
          <textarea
            aria-label="statement"
            value={statement}
            onChange={(e) => setStatement(e.target.value)}
          />
        </div>
        <div>
          <div className="label">Preview</div>
          <div className="panel">
            <Tex>{statement}</Tex>
          </div>
          <button className="primary" disabled={!source || !statement.trim()} onClick={save}>
            Save
          </button>
        </div>
      </div>

      <div className="panel entered">
        <div className="label">Entered today</div>
        <ul style={{ listStyle: 'none', padding: 0, margin: 0 }}>
          {entered.map((note) => (
            <EnteredNote
              key={note.id}
              note={note}
              onChange={(next) =>
                setEntered((prior) =>
                  next
                    ? prior.map((n) => (n.id === note.id ? next : n))
                    : prior.filter((n) => n.id !== note.id),
                )
              }
            />
          ))}
        </ul>
      </div>
    </div>
  );
}

function CreateSource({ onCreated }: { onCreated: (s: Source) => void }) {
  const [author, setAuthor] = useState('');
  const [year, setYear] = useState('');
  const [publication, setPublication] = useState('');
  const ready = author.trim() !== '' && /^\d{1,4}$/.test(year);
  return (
    <div className="panel">
      <input
        aria-label="author"
        placeholder="author"
        value={author}
        onChange={(e) => setAuthor(e.target.value)}
      />
      <input
        aria-label="year"
        placeholder="year"
        value={year}
        onChange={(e) => setYear(e.target.value)}
      />
      <input
        aria-label="publication"
        placeholder="publication (optional)"
        value={publication}
        onChange={(e) => setPublication(e.target.value)}
      />
      <button
        className="primary"
        disabled={!ready}
        onClick={() => {
          void api
            .createSource({ author, year: Number(year), publication: publication || null })
            .then(onCreated);
        }}
      >
        Create source
      </button>
    </div>
  );
}

/**
 * One line of `Entered today`. The controls are present only while the note has
 * no placement — design/app/Entry.md#entered-today.
 */
function EnteredNote({ note, onChange }: { note: Note; onChange: (next: Note | null) => void }) {
  const [editing, setEditing] = useState(false);
  const [draft, setDraft] = useState(note.statement);

  if (editing) {
    return (
      <li>
        <input
          aria-label={`edit note ${note.id}`}
          value={draft}
          onChange={(e) => setDraft(e.target.value)}
        />
        <button
          onClick={() => {
            void api.editNote(note.id, draft).then((next) => {
              onChange(next);
              setEditing(false);
            });
          }}
        >
          Save
        </button>
      </li>
    );
  }

  return (
    <li>
      <span className="id">{note.id}</span>
      <span className="statement">{note.statement}</span>
      {!note.placed && (
        <>
          <button
            className="link"
            aria-label={`edit note ${note.id}`}
            onClick={() => setEditing(true)}
          >
            ✎
          </button>
          <button
            className="link"
            aria-label={`delete note ${note.id}`}
            onClick={() => {
              void api.deleteNote(note.id).then(() => onChange(null));
            }}
          >
            ✕
          </button>
        </>
      )}
    </li>
  );
}
