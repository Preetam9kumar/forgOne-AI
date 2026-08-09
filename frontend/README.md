# AI Manufacturing Decision Copilot — Frontend

React (Vite) + Tailwind. Talks to the backend API only — no direct Azure calls from the
browser, no supplier-contact actions anywhere in this app.

## Design direction

Grounded in the actual manufacturing-floor artifact this tool replaces: a QC traveler /
routing card. Every eligibility outcome renders as an ink-stamp mark (PASS / FAIL / HOLD —
NO DATA / HOLD — CONFLICT) — the same visual device used consistently everywhere a status
appears, so a reviewer learns it once. Citations render as small dashed-edge tags, echoing a
physical inspection tag. Palette and type are documented in `tailwind.config.js`
(`paper` / `ink` / `steel` core palette, `stamp.*` for the four eligibility states, IBM Plex
Mono for technical/data text, IBM Plex Sans for body copy).

## Quickstart

```bash
npm install
npm run dev          # http://localhost:5173, expects the backend on http://localhost:8000
```

Point at a different backend URL by setting `VITE_API_BASE_URL` (see `.env.example`).
If the backend is configured with API-key-protected ingestion, set `VITE_INGEST_API_KEY` too.

On first load the app checks for data; if the backend DB is empty it shows a **Load challenge
pack** screen that calls `POST /ingest` — no manual curl needed to demo it.

## What's here

| Component | Role |
|---|---|
| `StampBadge` | The signature visual — renders any of the 4 eligibility states as an ink stamp |
| `RoutingCard` | One supplier's mandatory-constraint screen as a sequence of stamped checkpoints; click a checkpoint to pull its grounded explanation |
| `ShortlistManifest` | Ranked eligible suppliers + a "held" list for excluded ones with their reason |
| `PriorityDials` | Weight sliders (+ 3 presets) driving `/rankings` — this is the sensitivity-analysis UI |
| `ExplainDrawer` | Grounded explanation + citation tags for whichever checkpoint was last inspected |

## Build

```bash
npm run build     # verified clean in this repo -- 3 files output to dist/
npm run preview   # serve the production build locally
```

Deploys to Azure Static Web Apps as-is — connect the repo in the Azure portal and it
generates its own GitHub Actions workflow.

## Known gaps

- No loading skeletons — the "Loading…" state is a plain text line, not styled.
- No error boundary beyond the top-level fetch try/catch.
- `/explain` will legitimately return "Not found in source." for fields the sample pack's
  `evidence_text` doesn't cover in prose (e.g. capacity, lead time) — the structured
  `supplier_facts` still drive eligibility correctly either way; only the free-text
  explanation is thinner for those fields in the synthetic sample data.
