const BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000'
const INGEST_API_KEY = import.meta.env.VITE_INGEST_API_KEY

async function request(path, options = {}) {
  const res = await fetch(`${BASE_URL}${path}`, options)
  if (!res.ok) {
    const body = await res.text()
    throw new Error(`${options.method || 'GET'} ${path} -> ${res.status}: ${body}`)
  }
  return res.json()
}

export const api = {
  ingest: (packData) =>
    request('/ingest', {
      method: 'POST',
      headers: {
        ...(INGEST_API_KEY ? { 'X-API-KEY': INGEST_API_KEY } : {}),
        ...(packData ? { 'Content-Type': 'application/json' } : {}),
      },
      body: packData ? JSON.stringify(packData) : undefined,
    }),
  eligibility: () => request('/eligibility'),
  rankings: (weights) => {
    const params = new URLSearchParams({
      w_price: weights.price,
      w_lead_time: weights.lead_time_days,
      w_quality: weights.quality_score,
      w_sustainability: weights.sustainability_score,
    })
    return request(`/rankings?${params}`)
  },
  baseline: () => request('/rankings/baseline'),
  explain: (supplierId, criterion) =>
    request(`/suppliers/${supplierId}/explain?criterion=${encodeURIComponent(criterion)}`),
}
