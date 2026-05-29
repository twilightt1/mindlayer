from fastapi import APIRouter
from app.api.v1 import auth, users, chat, admin, system_settings
from app.api.v1 import memories, entities, sources

api_router = APIRouter(prefix="/api/v1")
api_router.include_router(auth.router)
api_router.include_router(users.router)
api_router.include_router(chat.router)
api_router.include_router(admin.router)
api_router.include_router(system_settings.router)

# MindLayer second-brain routes
api_router.include_router(memories.router)
api_router.include_router(entities.router)
api_router.include_router(entities.relations_router)  # /relations
api_router.include_router(entities.graph_router)   # /graph/snapshot, /graph/related/...
api_router.include_router(sources.router)
