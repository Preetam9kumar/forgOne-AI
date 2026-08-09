import { useState } from 'react'
import StampBadge from './StampBadge'

function fieldLabel(field) {
  return field.replaceAll('_', ' ')
}

/** One supplier's mandatory-constraint screen, presented as a routing /
 * traveler card: a fixed sequence of inspection stations, each stamped.
 * Order is used for its real meaning here -- a stable checklist a reviewer
 * can scan left to right, not an implied dependency between checks. */
export default function RoutingCard({ supplier, onInspect }) {
  const [openField, setOpenField] = useState(null)

  return (
    <div className="border border-ink bg-paper/60">
      <div className="flex items-center justify-between px-4 py-2.5 border-b border-ink">
        <div>
          <p className="font-mono text-[10px] tracking-widest text-ink-soft uppercase">
            Supplier {supplier.supplier_id}
          </p>
          <h3 className="font-semibold">{supplier.supplier_name}</h3>
        </div>
        <StampBadge status={supplier.eligible ? 'pass' : 'fail'} />
      </div>

      <ol className="divide-y divide-paper-line">
        {supplier.checks.map((check, i) => (
          <li key={check.field}>
            <button
              onClick={() => {
                const next = openField === check.field ? null : check.field
                setOpenField(next)
                if (next) onInspect(supplier.supplier_id, check.field)
              }}
              className="w-full flex items-center gap-3 px-4 py-2.5 text-left hover:bg-paper-line/30 transition-colors"
            >
              <span className="font-mono text-[11px] text-ink-soft w-6 shrink-0">
                {String(i + 1).padStart(2, '0')}
              </span>
              <span className="flex-1 text-sm capitalize">{fieldLabel(check.field)}</span>
              <StampBadge status={check.status} small />
            </button>
            {openField === check.field && (
              <p className="px-4 pb-3 pl-13 font-mono text-xs text-ink-soft leading-relaxed">
                {check.reason}
              </p>
            )}
          </li>
        ))}
      </ol>
    </div>
  )
}
