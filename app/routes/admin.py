import os
from pathlib import Path
from fastapi import APIRouter, Depends, HTTPException

from ..models import AdminStatusResponse, AdminSetupResponse
from ..config import get_settings, Settings
from ..dependencies import verify_api_key, get_openai_client

router = APIRouter(prefix="/admin", dependencies=[Depends(verify_api_key)])

HANDBOOK_PATH = Path(__file__).parent.parent.parent / "HANDBOOK_MAIN (2).md"


@router.get("/status", response_model=AdminStatusResponse)
async def get_status(
    settings: Settings = Depends(get_settings),
    client=Depends(get_openai_client),
):
    if not settings.vector_store_id:
        raise HTTPException(status_code=404, detail="VECTOR_STORE_ID not configured")

    vs = await client.vector_stores.retrieve(settings.vector_store_id)
    file_count = vs.file_counts.completed if vs.file_counts else 0

    return AdminStatusResponse(
        vector_store_id=vs.id,
        status=vs.status,
        file_count=file_count,
    )


@router.post("/setup", response_model=AdminSetupResponse)
async def setup_knowledge_base(
    settings: Settings = Depends(get_settings),
    client=Depends(get_openai_client),
):
    if not HANDBOOK_PATH.exists():
        raise HTTPException(status_code=500, detail=f"Handbook not found at {HANDBOOK_PATH}")

    # Upload the file
    with open(HANDBOOK_PATH, "rb") as f:
        uploaded = await client.files.create(file=f, purpose="assistants")

    # Create vector store and add file
    vs = await client.vector_stores.create(name="30DLC_Handbook")
    await client.vector_stores.files.create(vector_store_id=vs.id, file_id=uploaded.id)

    return AdminSetupResponse(
        vector_store_id=vs.id,
        message=f"Vector store created. Set VECTOR_STORE_ID={vs.id} in your .env and restart.",
    )
