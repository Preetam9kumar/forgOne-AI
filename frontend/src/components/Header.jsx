export default function Header({ productName, stats }) {
  return (
    <header className="border-b-2 border-ink px-6 py-4 flex items-end justify-between flex-wrap gap-3">
      <div>
        <p className="font-mono text-xs tracking-[0.2em] text-ink-soft uppercase">
          AI Hackathon — Track 01 · Supplier Shortlisting
        </p>
        <h1 className="font-mono text-2xl md:text-3xl font-semibold tracking-tight mt-1">
          ForgeOne AI <span className="text-steel-soft font-normal text-xl md:text-2xl">| Decision Copilot</span>
        </h1>
      </div>
      <dl className="font-mono text-xs text-ink-soft flex gap-5 tabular-nums">
        <div>
          <dt className="uppercase tracking-wide">Product</dt>
          <dd className="text-ink text-sm mt-0.5">{productName || '—'}</dd>
        </div>
        <div>
          <dt className="uppercase tracking-wide">Eligible</dt>
          <dd className="text-ink text-sm mt-0.5">{stats.eligible} / {stats.total}</dd>
        </div>
      </dl>
    </header>
  )
}
