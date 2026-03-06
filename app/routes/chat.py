import uuid
from fastapi import APIRouter, Depends, Request
from slowapi import Limiter
from slowapi.util import get_remote_address

from ..models import ChatRequest, ChatResponse, SessionDeleteResponse
from ..config import get_settings, Settings
from ..dependencies import verify_api_key, get_openai_client
from ..services import openai_service
from ..services.session_store import get_session_store

router = APIRouter()
limiter = Limiter(key_func=get_remote_address)


@router.post("/chat", response_model=ChatResponse, dependencies=[Depends(verify_api_key)])
@limiter.limit("10/minute")
async def chat_endpoint(
    request: Request,
    body: ChatRequest,
    settings: Settings = Depends(get_settings),
    client=Depends(get_openai_client),
):
    session_id = body.session_id or str(uuid.uuid4())

    answer, response_id = await openai_service.chat(
        client=client,
        session_id=session_id,
        user_message=body.message,
        vector_store_id=settings.vector_store_id,
        model=settings.model,
        max_tokens=settings.max_tokens,
    )

    return ChatResponse(session_id=session_id, answer=answer, response_id=response_id)


@router.delete("/sessions/{session_id}", response_model=SessionDeleteResponse, dependencies=[Depends(verify_api_key)])
async def clear_session(session_id: str):
    store = get_session_store()
    cleared = store.clear_session(session_id)
    return SessionDeleteResponse(session_id=session_id, cleared=cleared)
