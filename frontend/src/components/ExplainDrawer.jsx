/** Citations render as small dashed-edge tags -- echoing the paper tags
 * hung on a physical part after inspection, each stamped with where the
 * finding came from. */
export default function ExplainDrawer({ inspection, onClose }) {
  if (!inspection) return null
  const { supplierId, field, loading, result, error } = inspection

  return (
    <div className="border-2 border-ink bg-paper">
      <div className="flex items-center justify-between px-4 py-2.5 border-b border-ink bg-ink text-paper">
        <div>
          <p className="font-mono text-[10px] tracking-widest uppercase">Evidence lookup</p>
          <h2 className="font-semibold text-sm capitalize">
            {supplierId} — {field.replaceAll('_', ' ')}
          </h2>
        </div>
        <button
          onClick={onClose}
          className="font-mono text-[10px] uppercase border border-paper px-2 py-1 hover:bg-paper hover:text-ink transition-colors shrink-0"
        >
          Close
        </button>
      </div>

      <div className="px-4 py-3">
        {loading && <p className="font-mono text-xs text-ink-soft">Retrieving source evidence…</p>}
        {error && <p className="font-mono text-xs text-stamp-fail">{error}</p>}
        {result && (
          <>
            <p className="text-sm leading-relaxed mb-3">{result.explanation}</p>
            {result.citations.length > 0 ? (
              <div className="flex flex-wrap gap-2">
                {result.citations.map((c, i) => (
                  <span
                    key={i}
                    className="inline-flex items-center gap-1.5 font-mono text-[10px] border border-dashed border-ink-soft px-2 py-1 text-ink-soft"
                  >
                    <span className="text-ink">{c.doc_id}</span>
                    <span>/ {c.source_field}</span>
                  </span>
                ))}
              </div>
            ) : (
              <p className="font-mono text-[10px] text-ink-soft uppercase tracking-wide">
                No source citation available
              </p>
            )}
          </>
        )}
      </div>
    </div>
  )
}
