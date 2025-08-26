from fastapi import FastAPI
from fastapi.routing import APIRoute
from fastmcp import FastMCP
from starlette.middleware.cors import CORSMiddleware

from alfred.api.main import api_router
from alfred.api.routes import vcell
from alfred.api.routes.med_ai import mcpRouter
from alfred.core.config import settings


def custom_generate_unique_id(route: APIRoute) -> str:
    return f"{route.tags[0]}-{route.name}"

mcp = FastMCP("Root")
# mcp.mount(mcpRouter)
mcp.mount(vcell.mcpRouter)
mcp_http = mcp.http_app(path="/mcp")


app = FastAPI(
    title=settings.PROJECT_NAME,
    openapi_url=f"/openapi.json",
    generate_unique_id_function=custom_generate_unique_id,
    root_path=f"{settings.API_V1_STR}",
    lifespan=mcp_http.lifespan
)

# Set all CORS enabled origins
if settings.all_cors_origins:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.all_cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

# app.include_router(api_router, prefix=settings.API_V1_STR)

# 1. Generate MCP server from your API

app.include_router(api_router)
app.mount("/", mcp_http)


# mcp.run(transport="http")


