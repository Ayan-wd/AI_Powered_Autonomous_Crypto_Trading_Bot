"""
Configuration viewer endpoint with secrets safely sanitized.
"""

from fastapi import APIRouter
from backend.app.core.config import settings

router = APIRouter(prefix="/config", tags=["Configuration"])


@router.get("")
async def get_sanitized_config():
    """Retrieve runtime configuration with all secrets and credentials redacted."""
    return settings.sanitized_dict()
