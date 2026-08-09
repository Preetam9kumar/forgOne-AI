# AI Manufacturing Decision Copilot — Backend (Track 1: Supplier Shortlisting)

Decision-support only. This API has no endpoint that contacts a supplier, sends an RFQ,
approves a vendor, or places an order — enforced structurally (see `tests/test_api.py::test_no_endpoint_exists_for_supplier_approval_or_contact`), not just by convention.

## What's implemented

| Layer | Status | Notes |
|---|---|---|
| Eligibility engine | ✅ Deterministic, 10 unit tests | No LLM in the decision path |
| Ranking + sensitivity | ✅ Deterministic, 7 unit tests | Weighted, normalized scoring |
| Ingestion pipeline | ✅ 7 unit tests | Loads a challenge-pack-shaped JSON into the DB |
| Grounded explanation (RAG) | ✅ 5 unit tests, DB-keyword retriever wired by default | Real Azure AI Foundry + AI Search wiring included, needs live credentials |
| FastAPI app | ✅ 11 integration tests, verified with a live `curl` run | |
| Eval metrics | ✅ 7 unit tests | Maps directly to the brief's required metrics |

**59/59 tests passing.** Run them yourself: `pytest -v`.

## Quickstart (local, no Azure needed)

```bash
python3 -m venv .venv
./.venv/bin/pip install -r requirements.txt
./.venv/bin/uvicorn app.api.main:app --reload
```

Then in another terminal:
```bash
curl -X POST http://127.0.0.1:8000/ingest          # loads the sample pack
curl http://127.0.0.1:8000/eligibility
curl http://127.0.0.1:8000/rankings
curl "http://127.0.0.1:8000/suppliers/aster/explain?criterion=certification"
```

Interactive API docs: `http://127.0.0.1:8000/docs`

## The sample data

`data/sample_challenge_pack.json` is **synthetic** — replace it with the organizer-supplied
Manufacturing Challenge Pack before evaluation (same shape: `product.requirements` +
`suppliers[].facts/.quotation/.evidence_text`). It's deliberately built to exercise the
brief's three required demo cases in one file:

| Supplier | Case | What it demonstrates |
|---|---|---|
| `aster` | Clean pass | All mandatory constraints satisfied with clear source citations |
| `borealis` | Missing data | `lead_time_days` has no source fact → `insufficient_data`, not a guess |
| `crestpoint` | Conflicting data | `capacity_units_per_month` disagrees across two source docs → `conflicting_data`, both values surfaced |
| `deltaforge` | Hard failure | Missing mandatory ISO9001 certification → `fail` |
| `eastwind` | Sensitivity demo | Priciest + fastest supplier — ranks #1 under default weights, drops under `cost_priority` (see `sensitivity_analysis` test) |

## API reference

| Endpoint | Purpose |
|---|---|
| `POST /ingest` | Load the challenge pack into the DB from the default sample file or an uploaded JSON payload (admin-only in production) |
| `GET /eligibility` | Eligibility screen for every supplier |
| `GET /suppliers/{id}/eligibility` | Eligibility screen for one supplier |
| `GET /rankings?w_price=&w_lead_time=&w_quality=&w_sustainability=` | Ranked shortlist (eligible suppliers only) + why others were excluded |
| `GET /rankings/sensitivity` | Rank of every eligible supplier under 4 preset weight scenarios |
| `GET /rankings/baseline` | Price-only baseline ranking, for the brief's required baseline comparison |
| `GET /suppliers/{id}/explain?criterion=` | Grounded natural-language explanation + citations |
| `GET /metrics` | Runtime metrics snapshot for uptime, request volume, and response health |

## Wiring up real Azure AI Foundry + Azure AI Search

The app runs fully offline by default (`_DbKeywordRetriever` + `_EchoLLM` in
`app/services/explain_service.py`) so it's demoable with zero cloud setup. To switch to the
real hybrid-retrieval + LLM explanation chain:

1. Deploy an embedding model in Azure AI Foundry. Recommended model:
   - `text-embedding-3-large`
2. Deploy a chat model in Azure AI Foundry. Recommended model:
   - `gpt-4o-mini`
3. Create an Azure AI Search index with the following fields:
   - `chunk_id` (key/string)
   - `supplier_id` (string, filterable)
   - `doc_id` (string, filterable)
   - `source_field` (string, filterable)
   - `content` (searchable text)
   - `content_vector` (`Collection(Edm.Single)` vector field)
4. Copy `.env.example` to `.env` and fill in the Azure Foundry/Search values.
   The backend now supports either:
   - Azure AI Foundry project-endpoint auth with `AZURE_AI_PROJECT_ENDPOINT` and `AZURE_AI_API_KEY`, or
   - Azure OpenAI API-key auth with `AZURE_OPENAI_ENDPOINT` and `AZURE_OPENAI_API_KEY`.
5. Optional: configure `AUTH_MODE=azure_ad` to protect `/ingest` behind Azure AD.
   Set `AZURE_AD_TENANT_ID`, `AZURE_AD_CLIENT_ID`, and optionally `AZURE_AD_AUDIENCE`.
6. If `/ingest` is called from a script or CLI tool, you can also use
   `AUTH_MODE=api_key` and `INGEST_API_KEY=<secret>`.
7. If Azure Search is configured, `POST /ingest` will also synchronize evidence chunks
   into the index automatically.
8. Authenticate locally with `az login`, or use Container Apps Managed Identity in
   production (`DefaultAzureCredential` picks it up automatically).

## Monitoring

The backend exposes a lightweight runtime metrics endpoint at `GET /metrics`.
It reports uptime, request volume, success/client/server error counts, and average response latency.
Use this endpoint for health dashboards or to connect a Prometheus/Grafana exporter in Azure Container Apps.

## Database migrations

This backend now supports Alembic migrations for production schema management.

- Install dependencies: `pip install -r requirements.txt`
- Initialize your DB schema with `alembic upgrade head`
- To add a schema change, create a new revision:
  `alembic revision --autogenerate -m "describe change"`
- Then apply it with `alembic upgrade head`

## Running tests

```bash
./.venv/bin/pytest -v          # full suite (59 tests)
./.venv/bin/pytest tests/test_eligibility.py -v   # one module
```

Tests run against isolated in-memory SQLite — no external services required, including for
the RAG chain (it's tested against fake retriever/LLM implementations — see
`tests/test_rag_chain.py`).

## Docker

```bash
docker build -t manuf-copilot-api .
docker run -p 8000:8000 manuf-copilot-api
```

Matches the Azure Container Apps deployment target in the architecture doc — same image,
`az acr build` + `az containerapp update` to ship it.

## Project layout

```
app/
  eligibility/   deterministic constraint checking
  ranking/       weighted scoring + sensitivity analysis
  ingest/        challenge-pack JSON -> DB
  rag/           grounded explanation chain (fake-testable + real Azure wiring)
  services/      adapts DB rows <-> the pure engines above
  api/           FastAPI app + routers
  eval/          brief-required evaluation metrics
tests/           59 tests, one module per layer above
data/            sample_challenge_pack.json (synthetic — replace with the real pack)
```

## Known limitations (documented, not hidden)

- `quality_score` is currently proxied from `sustainability_score` in the sample data — the
  real challenge pack should supply a dedicated quality/historical-performance field; swap it
  in `app/services/ranking_service.py::_quality_score`.
- The default `_DbKeywordRetriever` is a simple keyword matcher, not semantic search — it's a
  zero-dependency fallback, not a substitute for the real Azure AI Search hybrid retriever.
- `/ingest` can now be protected in production with `AUTH_MODE=api_key` or `AUTH_MODE=azure_ad`; use Entra ID or a vault-backed API key for Admin ingestion.
