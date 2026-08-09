const DIALS = [
  { key: 'price', label: 'Cost' },
  { key: 'lead_time_days', label: 'Speed' },
  { key: 'quality_score', label: 'Quality' },
  { key: 'sustainability_score', label: 'Sustainability' },
]

const PRESETS = {
  balanced: { price: 0.35, lead_time_days: 0.25, quality_score: 0.25, sustainability_score: 0.15 },
  cost_priority: { price: 0.6, lead_time_days: 0.15, quality_score: 0.15, sustainability_score: 0.10 },
  speed_priority: { price: 0.15, lead_time_days: 0.6, quality_score: 0.15, sustainability_score: 0.10 },
}

export default function PriorityDials({ weights, onChange }) {
  return (
    <div className="border border-ink px-4 py-3">
      <div className="flex items-center justify-between mb-3">
        <p className="font-mono text-[10px] tracking-widest uppercase text-ink-soft">
          Priority calibration
        </p>
        <div className="flex gap-1.5">
          {Object.keys(PRESETS).map((name) => (
            <button
              key={name}
              onClick={() => onChange(PRESETS[name])}
              className="font-mono text-[10px] uppercase tracking-wide border border-ink px-2 py-1 hover:bg-ink hover:text-paper transition-colors"
            >
              {name.replace('_priority', '')}
            </button>
          ))}
        </div>
      </div>

      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        {DIALS.map((dial) => (
          <label key={dial.key} className="block">
            <div className="flex justify-between font-mono text-[11px] text-ink-soft mb-1">
              <span className="uppercase tracking-wide">{dial.label}</span>
              <span className="tabular-nums">{Math.round(weights[dial.key] * 100)}</span>
            </div>
            <input
              type="range"
              min="0"
              max="100"
              value={Math.round(weights[dial.key] * 100)}
              onChange={(e) => onChange({ ...weights, [dial.key]: Number(e.target.value) / 100 })}
              className="w-full accent-steel"
              aria-label={`${dial.label} weight`}
            />
          </label>
        ))}
      </div>
    </div>
  )
}
