import { useEffect, useState, useCallback, useRef } from 'react'
import { api } from './api'
import Header from './components/Header'
import BoundaryStrip from './components/BoundaryStrip'
import RoutingCard from './components/RoutingCard'
import ShortlistManifest from './components/ShortlistManifest'
import PriorityDials from './components/PriorityDials'
import ExplainDrawer from './components/ExplainDrawer'
import { SkeletonCard, SkeletonManifest } from './components/SkeletonLoader'

const DEFAULT_WEIGHTS = {
  price: 0.35,
  lead_time_days: 0.25,
  quality_score: 0.25,
  sustainability_score: 0.15,
}

export default function App() {
  const [eligibility, setEligibility] = useState([])
  const [rankingData, setRankingData] = useState({ ranked: [], excluded: [] })
  const [weights, setWeights] = useState(DEFAULT_WEIGHTS)
  const [inspection, setInspection] = useState(null)
  const [status, setStatus] = useState('loading') // loading | ready | needs-ingest | error
  const [errorMsg, setErrorMsg] = useState(null)
  const [showUploadModal, setShowUploadModal] = useState(false)
  const fileInputRef = useRef(null)

  const loadAll = useCallback(async (currentWeights) => {
    try {
      const [elig, rank] = await Promise.all([api.eligibility(), api.rankings(currentWeights)])
      setEligibility(elig)
      setRankingData(rank)
      setStatus('ready')
    } catch (err) {
      setStatus('needs-ingest')
      setErrorMsg(err.message)
    }
  }, [])

  useEffect(() => {
    loadAll(DEFAULT_WEIGHTS)
  }, [loadAll])

  const handleWeightsChange = (next) => {
    setWeights(next)
    loadAll(next)
  }

  const handleIngestDefault = async () => {
    setStatus('loading')
    setErrorMsg(null)
    try {
      await api.ingest()
      await loadAll(weights)
      setShowUploadModal(false)
    } catch (err) {
      setStatus('needs-ingest')
      setErrorMsg(err.message)
    }
  }

  const handleFileUpload = (e) => {
    const file = e.target.files?.[0]
    if (!file) return

    const reader = new FileReader()
    reader.onload = async (event) => {
      try {
        const json = JSON.parse(event.target?.result)
        setStatus('loading')
        setErrorMsg(null)
        await api.ingest(json)
        await loadAll(weights)
        setShowUploadModal(false)
      } catch (err) {
        setStatus('needs-ingest')
        setErrorMsg(`Failed to ingest custom pack: ${err.message}`)
      }
    }
    reader.readAsText(file)
  }

  const handleInspect = async (supplierId, field) => {
    setInspection({ supplierId, field, loading: true, result: null, error: null })
    try {
      const result = await api.explain(supplierId, field)
      setInspection({ supplierId, field, loading: false, result, error: null })
    } catch (err) {
      setInspection({ supplierId, field, loading: false, result: null, error: err.message })
    }
  }

  const stats = {
    total: eligibility.length,
    eligible: eligibility.filter((s) => s.eligible).length,
  }

  if (status === 'needs-ingest' || status === 'error') {
    return (
      <div className="min-h-screen flex items-center justify-center px-6 py-12">
        <div className="border-2 border-ink bg-paper px-8 py-6 max-w-lg text-center space-y-4">
          <p className="font-mono text-[10px] tracking-widest uppercase text-ink-soft">
            Setup required
          </p>
          <h1 className="font-semibold text-xl">No Challenge Pack Loaded</h1>
          <p className="text-sm text-ink-soft">
            Load the default synthetic challenge pack or upload a custom challenge pack JSON file to evaluate suppliers.
          </p>

          <div className="flex flex-col sm:flex-row gap-3 justify-center pt-2">
            <button
              onClick={handleIngestDefault}
              className="font-mono text-xs uppercase tracking-wide border-2 border-ink px-4 py-2 hover:bg-ink hover:text-paper transition-colors"
            >
              Load Sample Data
            </button>

            <button
              onClick={() => fileInputRef.current?.click()}
              className="font-mono text-xs uppercase tracking-wide border-2 border-steel text-steel px-4 py-2 hover:bg-steel hover:text-paper transition-colors"
            >
              Upload Custom JSON
            </button>
            <input
              type="file"
              ref={fileInputRef}
              onChange={handleFileUpload}
              accept=".json"
              className="hidden"
            />
          </div>

          {errorMsg && (
            <p className="font-mono text-[11px] text-stamp-fail mt-3 break-words text-left bg-stamp-fail/10 p-2 border border-stamp-fail">
              {errorMsg}
            </p>
          )}
        </div>
      </div>
    )
  }

  return (
    <div className="min-h-screen">
      <Header productName="Precision Enclosure Assembly" stats={stats} />
      <BoundaryStrip />

      <main className="px-6 py-6 max-w-6xl mx-auto space-y-6">
        <div className="flex items-center justify-between">
          <PriorityDials weights={weights} onChange={handleWeightsChange} />
        </div>

        <div className="flex justify-end">
          <button
            onClick={() => setShowUploadModal(true)}
            className="font-mono text-[10px] uppercase tracking-wider border border-ink px-3 py-1 hover:bg-ink hover:text-paper transition-colors"
          >
            + Change Data Pack
          </button>
        </div>

        {showUploadModal && (
          <div className="fixed inset-0 bg-ink/40 flex items-center justify-center p-4 z-50">
            <div className="border-2 border-ink bg-paper p-6 max-w-md w-full space-y-4 shadow-xl">
              <div className="flex justify-between items-center border-b border-ink pb-2">
                <h3 className="font-semibold text-sm uppercase font-mono">Ingest Challenge Pack</h3>
                <button
                  onClick={() => setShowUploadModal(false)}
                  className="font-mono text-xs border border-ink px-2 py-0.5 hover:bg-ink hover:text-paper"
                >
                  ✕
                </button>
              </div>
              <p className="text-xs text-ink-soft">
                Choose to reload the standard benchmark dataset or upload a new JSON pack payload.
              </p>
              <div className="flex flex-col gap-2 pt-2">
                <button
                  onClick={handleIngestDefault}
                  className="font-mono text-xs uppercase border border-ink p-2 text-center hover:bg-ink hover:text-paper"
                >
                  Reload Sample Data
                </button>
                <button
                  onClick={() => fileInputRef.current?.click()}
                  className="font-mono text-xs uppercase border border-steel text-steel p-2 text-center hover:bg-steel hover:text-paper"
                >
                  Upload JSON File
                </button>
              </div>
            </div>
          </div>
        )}

        <div className="grid md:grid-cols-2 gap-6 items-start">
          <div className="space-y-4">
            <p className="font-mono text-[10px] tracking-widest uppercase text-ink-soft">
              Eligibility screen — routing cards
            </p>
            <div className="space-y-4">
              {status === 'loading' ? (
                <>
                  <SkeletonCard />
                  <SkeletonCard />
                </>
              ) : (
                eligibility.map((s) => (
                  <RoutingCard key={s.supplier_id} supplier={s} onInspect={handleInspect} />
                ))
              )}
            </div>
          </div>

          <div className="space-y-4">
            <p className="font-mono text-[10px] tracking-widest uppercase text-ink-soft">
              Ranking
            </p>
            {status === 'loading' ? (
              <SkeletonManifest />
            ) : (
              <ShortlistManifest ranked={rankingData.ranked} excluded={rankingData.excluded} />
            )}
            <ExplainDrawer inspection={inspection} onClose={() => setInspection(null)} />
          </div>
        </div>
      </main>
    </div>
  )
}

