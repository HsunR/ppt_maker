from fastapi import APIRouter
from service.schemas.models import STYLES_CATALOG

router = APIRouter()

@router.get("/api/styles")
def list_styles():
    return STYLES_CATALOG

@router.get("/api/styles/{style_id}")
def get_style(style_id: str):
    for s in STYLES_CATALOG:
        if s.id == style_id:
            return s
    from fastapi import HTTPException
    raise HTTPException(404, f"Style '{style_id}' not found")