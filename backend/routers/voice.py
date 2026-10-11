from fastapi import APIRouter, HTTPException, Response, UploadFile

from services import stt_service, tts_service

router = APIRouter()


@router.post("/transcribe")
async def transcribe(file: UploadFile):
    text = stt_service.transcribe(await file.read())
    if not text:
        raise HTTPException(422, "Could not transcribe — silent or unclear audio")
    return {"text": text}


@router.get("/tts")
def tts(text: str, lang: str = "en"):
    result = tts_service.synthesize(text, lang)
    if not result:
        raise HTTPException(503, "No TTS voice for that language, or offline")
    if isinstance(result, tuple):          # (bytes, mime) from multi-engine
        audio, mime = result
    else:                                  # plain bytes (older signature)
        audio, mime = result, "audio/mpeg"
    return Response(content=audio, media_type=mime)