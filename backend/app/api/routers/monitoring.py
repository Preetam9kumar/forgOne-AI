from fastapi import APIRouter

from app.metrics import metrics

router = APIRouter(tags=["monitoring"])


@router.get("/metrics")
def get_metrics() -> dict:
    return metrics.snapshot()
