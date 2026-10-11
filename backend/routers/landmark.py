from fastapi import APIRouter, HTTPException, UploadFile

from services import landmark_service

router = APIRouter()


@router.post("")
async def identify(file: UploadFile):
    if not (file.content_type or "").startswith("image/"):
        raise HTTPException(415, "Upload an image (jpg/png)")
    result = landmark_service.identify(await file.read(),
                                       file.content_type or "image/jpeg")
    if not result:
        raise HTTPException(503, "Recognition unavailable — try again")
    return result