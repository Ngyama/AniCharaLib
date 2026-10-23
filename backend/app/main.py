from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import get_settings
from app.routers import attributes, characters, works

app = FastAPI(
    title="AniCharaLib API",
    version="1.0.0",
    description="ACG character database: characters, works and a searchable attribute dictionary.",
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=get_settings().cors_origin_list,
    allow_methods=["GET"],
    allow_headers=["*"],
)
app.include_router(attributes.router)
app.include_router(characters.router)
app.include_router(works.router)


@app.get("/api/health", tags=["meta"])
def health() -> dict[str, str]:
    return {"status": "ok"}
