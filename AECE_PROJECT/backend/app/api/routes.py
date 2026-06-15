from fastapi import APIRouter

from app.api.aece_routes import router as aece_router


api_router = APIRouter()
api_router.include_router(aece_router)

