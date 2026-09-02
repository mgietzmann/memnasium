// Type-ahead over one endpoint, showing chips for the matches and offering **create** when
// nothing matches — the explicit-create rule of design/app/Fish.md. A name that does not match
// offers a create action rather than being made on submit, so a typo cannot silently mint a clade.

import { useEffect, useState, type ReactNode } from 'react';

export interface SearchFieldProps<T> {
  label: string;
  /** The query, held by the parent so a picked value can replace it. */
  query: string;
  onQueryChange: (query: string) => void;
  search: (query: string) => Promise<T[]>;
  optionKey: (item: T) => string;
  renderOption: (item: T) => ReactNode;
  onPick: (item: T) => void;
  /** Offered when nothing matches. Omitted where creating makes no sense. */
  onCreate?: (query: string) => void;
  /** Shown instead of the input once something is picked. */
  picked?: ReactNode;
  onClear?: () => void;
}

export function SearchField<T>({
  label,
  query,
  onQueryChange,
  search,
  optionKey,
  renderOption,
  onPick,
  onCreate,
  picked,
  onClear,
}: SearchFieldProps<T>) {
  const [matches, setMatches] = useState<T[]>([]);
  const [open, setOpen] = useState(false);

  useEffect(() => {
    if (picked !== undefined || query.trim() === '') {
      setMatches([]);
      return;
    }
    let live = true;
    void search(query).then((found) => {
      if (live) {
        setMatches(found);
        setOpen(true);
      }
    });
    return () => {
      live = false;
    };
  }, [query, picked, search]);

  if (picked !== undefined) {
    return (
      <div className="field">
        <span className="label">{label}</span>
        <div className="field-picked">
          <span>{picked}</span>
          <span className="known">✓ known</span>
          {onClear && (
            <button type="button" className="link" onClick={onClear}>
              change
            </button>
          )}
        </div>
      </div>
    );
  }

  return (
    <div className="field">
      <label className="label" htmlFor={`search-${label}`}>
        {label}
      </label>
      <input
        id={`search-${label}`}
        className="input"
        value={query}
        autoComplete="off"
        onChange={(event) => {
          onQueryChange(event.target.value);
        }}
      />
      {open && query.trim() !== '' && (
        <div className="results">
          {matches.map((item) => (
            <button
              key={optionKey(item)}
              type="button"
              className="result"
              onClick={() => {
                setOpen(false);
                onPick(item);
              }}
            >
              {renderOption(item)}
            </button>
          ))}
          {onCreate && (
            <button
              type="button"
              className="result result-create"
              onClick={() => {
                setOpen(false);
                onCreate(query.trim());
              }}
            >
              + create “{query.trim()}”
            </button>
          )}
        </div>
      )}
    </div>
  );
}
