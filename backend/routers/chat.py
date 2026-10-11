from fastapi import APIRouter

from services import chatbot_service

from backend.schemas import ChatRequest

router = APIRouter()


@router.post("")
def chat(body: ChatRequest):
    history = [{"role": m.role, "content": m.content} for m in body.history]
    reply = chatbot_service.get_reply(history, body.lang)
    return {"reply": reply, "lang": body.lang}


@router.get("/context-preview")
def context_preview():
    """Debug/inspection: the grounding block injected into every prompt."""
    return {"system_prompt": chatbot_service.build_system_prompt("en")}