from typing import Dict
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, Field
from starlette import status

from database.config import get_settings

home_route = APIRouter()


@home_route.get("/", response_model=str, summary="Home", description="Home page")
async def home(settings=Depends(get_settings)) -> str:
    try:
        return settings.APP_NAME
    except:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal error")


class HealthResponse(BaseModel):
    status: str = Field(..., description="app status ")

@home_route.get("/health",
                response_model=HealthResponse,
                status_code=status.HTTP_200_OK,
                summary="Health check",
                description="App health status")
async def health() -> HealthResponse:
    try:
        return HealthResponse(status="healthy")
    except:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Service is unavailable")