"""Admin-only ingestion trigger. In production, gate this behind real auth
(Entra ID) -- it's the only write path in the whole API, which is
deliberate: there is no endpoint anywhere that can contact, approve, or
order from a supplier."""
from pathlib import Path

from fastapi import APIRouter, Body, Depends
from sqlalchemy.orm import Session

from app.api.auth import get_admin_auth
from app.db import get_db
from app.ingest.pipeline import ingest_from_file, ingest_pack
from app.ingest.schemas import ChallengePackSchema

router = APIRouter(tags=["admin"])

DEFAULT_PACK_PATH = Path(__file__).resolve().parents[3] / "data" / "sample_challenge_pack.json"


@router.post("/ingest")
def trigger_ingest(
    pack: ChallengePackSchema | None = Body(default=None),
    db: Session = Depends(get_db),
    _: dict = Depends(get_admin_auth),
):
    if pack is None:
        summary = ingest_from_file(db, DEFAULT_PACK_PATH)
    else:
        summary = ingest_pack(db, pack)
    return summary
