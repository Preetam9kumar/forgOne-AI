function ScoreGauge({ value }) {
  // value is 0..1 -- rendered as a machined dial readout, not a generic progress bar.
  const pct = Math.round(value * 100)
  return (
    <div className="flex items-center gap-2 w-32">
      <div className="flex-1 h-2 bg-paper-line relative">
        <div className="absolute inset-y-0 left-0 bg-steel" style={{ width: `${pct}%` }} />
      </div>
      <span className="font-mono text-xs tabular-nums text-ink-soft w-9 text-right">{pct}%</span>
    </div>
  )
}

export default function ShortlistManifest({ ranked, excluded }) {
  return (
    <div className="border border-ink">
      <div className="px-4 py-2.5 border-b border-ink bg-ink text-paper">
        <p className="font-mono text-[10px] tracking-widest uppercase">Manifest</p>
        <h2 className="font-semibold">Ranked Shortlist</h2>
      </div>

      <div className="overflow-x-auto">
        <table className="w-full text-sm min-w-[400px]">
          <thead>
            <tr className="font-mono text-[10px] uppercase tracking-wide text-ink-soft border-b border-paper-line">
              <th className="text-left px-4 py-2 w-10">#</th>
              <th className="text-left px-2 py-2">Supplier</th>
              <th className="text-right px-2 py-2">Price</th>
              <th className="text-right px-2 py-2">Lead time</th>
              <th className="text-left px-4 py-2">Score</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-paper-line">
            {ranked.map((row) => (
              <tr key={row.supplier_id}>
                <td className="px-4 py-2.5 font-mono tabular-nums text-ink-soft">{row.rank}</td>
                <td className="px-2 py-2.5 font-medium">{row.supplier_id}</td>
                <td className="px-2 py-2.5 text-right font-mono tabular-nums">${row.price?.toFixed(2)}</td>
                <td className="px-2 py-2.5 text-right font-mono tabular-nums">{row.lead_time_days}d</td>
                <td className="px-4 py-2.5"><ScoreGauge value={row.score} /></td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {excluded.length > 0 && (
        <div className="border-t border-ink px-4 py-3">
          <p className="font-mono text-[10px] tracking-widest uppercase text-ink-soft mb-2">
            Held — not eligible ({excluded.length})
          </p>
          <ul className="space-y-1.5">
            {excluded.map((s) => (
              <li key={s.supplier_id} className="font-mono text-xs text-ink-soft">
                <span className="text-ink">{s.supplier_name}</span> — {s.reasons[0]}
              </li>
            ))}
          </ul>
        </div>
      )}
    </div>
  )
}
