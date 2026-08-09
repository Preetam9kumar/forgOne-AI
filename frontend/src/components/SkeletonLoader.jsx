export function SkeletonCard() {
  return (
    <div className="border border-paper-line bg-paper/60 p-4 space-y-3 animate-pulse">
      <div className="flex items-center justify-between border-b border-paper-line pb-2">
        <div className="space-y-1">
          <div className="h-2.5 w-20 bg-paper-line rounded" />
          <div className="h-4 w-36 bg-paper-line rounded" />
        </div>
        <div className="h-6 w-16 bg-paper-line rounded" />
      </div>
      <div className="space-y-2">
        {[1, 2, 3, 4].map((i) => (
          <div key={i} className="flex items-center justify-between py-1.5 border-b border-paper-line/50">
            <div className="h-3 w-4 bg-paper-line rounded" />
            <div className="h-3 w-32 bg-paper-line rounded" />
            <div className="h-5 w-12 bg-paper-line rounded" />
          </div>
        ))}
      </div>
    </div>
  )
}

export function SkeletonManifest() {
  return (
    <div className="border border-paper-line bg-paper animate-pulse space-y-3 p-4">
      <div className="h-5 w-32 bg-paper-line rounded mb-4" />
      {[1, 2, 3].map((i) => (
        <div key={i} className="flex items-center justify-between py-2 border-b border-paper-line/50">
          <div className="h-3 w-6 bg-paper-line rounded" />
          <div className="h-3 w-24 bg-paper-line rounded" />
          <div className="h-3 w-16 bg-paper-line rounded" />
          <div className="h-3 w-20 bg-paper-line rounded" />
        </div>
      ))}
    </div>
  )
}
