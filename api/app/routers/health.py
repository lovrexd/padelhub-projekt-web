from fastapi import APIRouter

router = APIRouter()


@router.get("/")
def health():
    """Jednostavna provjera radi li backend poslužitelj."""
    return {"status": "ok"}
