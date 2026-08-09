/** Quiet, stenciled-plate notice rather than a loud alert box — the
 * human-approval boundary is a fact of how the system works, not a
 * warning the user needs to react to. */
export default function BoundaryStrip() {
  return (
    <div className="border-y border-paper-line bg-paper px-6 py-2">
      <p className="font-mono text-[11px] tracking-wide text-ink-soft uppercase">
        Decision support only — no supplier is contacted, approved, or ordered from by this system.
      </p>
    </div>
  )
}
