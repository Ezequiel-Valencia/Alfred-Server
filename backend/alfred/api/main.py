from fastapi import APIRouter
from fastmcp import FastMCP

from alfred.api.routes import med_ai, vcell

api_router = APIRouter()
api_router.include_router(med_ai.router)
api_router.include_router(vcell.router)


# if settings.ENVIRONMENT == "local":
#     api_router.include_router(private.router)
