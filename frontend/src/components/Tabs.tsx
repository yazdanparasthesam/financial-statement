export interface TabDef { id: string; label: string }

export default function Tabs({ tabs, active, onChange }: { tabs: TabDef[]; active: string; onChange: (id: string) => void }) {
  return (
    <div className="mb-5 flex flex-wrap gap-1 border-b border-slate-200">
      {tabs.map((t) => (
        <button
          key={t.id}
          onClick={() => onChange(t.id)}
          className={`rounded-t-lg px-3.5 py-2 text-sm font-medium transition ${
            active === t.id
              ? 'border-b-2 border-brand-600 bg-brand-50 text-brand-700'
              : 'text-slate-500 hover:bg-slate-100 hover:text-slate-700'}`}
        >
          {t.label}
        </button>
      ))}
    </div>
  )
}
