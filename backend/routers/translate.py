from fastapi import APIRouter, Query

from services import translate_service

router = APIRouter()


@router.get("")
def translate(text: str = Query(min_length=1), lang: str = "en"):
    text_out, was_translated = translate_service.localized_text(text, lang)
    return {"text": text_out, "was_translated": was_translated}