// One row, one selection, contents swap beneath — design/app/Components.md.

export interface TabsProps<T extends string> {
  tabs: readonly T[];
  active: T;
  onChange: (tab: T) => void;
}

export function Tabs<T extends string>({ tabs, active, onChange }: TabsProps<T>) {
  return (
    <div className="tabs" role="tablist">
      {tabs.map((tab) => (
        <button
          key={tab}
          type="button"
          role="tab"
          aria-selected={tab === active}
          className={tab === active ? 'tab tab-active' : 'tab'}
          onClick={() => {
            onChange(tab);
          }}
        >
          {tab}
        </button>
      ))}
    </div>
  );
}
