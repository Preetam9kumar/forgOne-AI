const STAMP_CONFIG = {
  pass: { label: 'PASS', color: 'text-stamp-pass', border: 'border-stamp-pass', rot: '-4deg' },
  fail: { label: 'FAIL', color: 'text-stamp-fail', border: 'border-stamp-fail', rot: '3deg' },
  insufficient_data: { label: 'HOLD — NO DATA', color: 'text-stamp-hold', border: 'border-stamp-hold', rot: '-2deg' },
  conflicting_data: { label: 'HOLD — CONFLICT', color: 'text-stamp-hold' /* uses conflict below */, border: 'border-stamp-conflict', rot: '5deg' },
}

// Conflict status gets its own color; keep the map above simple and override here.
const COLOR_OVERRIDE = { conflicting_data: 'text-stamp-conflict' }

/** The signature visual device: every eligibility outcome renders as an
 * ink-stamp mark, the way a QC traveler card gets stamped station by
 * station on a factory floor. Same component, same four states, used
 * everywhere a status appears in this app. */
export default function StampBadge({ status, small = false }) {
  const cfg = STAMP_CONFIG[status] || STAMP_CONFIG.fail
  const color = COLOR_OVERRIDE[status] || cfg.color
  return (
    <span
      className={`inline-flex items-center justify-center border-2 ${cfg.border} ${color}
                  font-mono font-semibold tracking-wide uppercase
                  ${small ? 'text-[10px] px-1.5 py-0.5' : 'text-xs px-2.5 py-1'}
                  animate-stampdown select-none`}
      style={{ '--stamp-rot': cfg.rot, transform: `rotate(${cfg.rot})` }}
    >
      {cfg.label}
    </span>
  )
}
