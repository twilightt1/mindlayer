from fastapi import APIRouter
from app.api.v1 import auth, users, chat, admin, system_settings
from app.api.v1 import memories, entities, sources, insights, discovery, workspaces
from app.api.v1 import demo, analytics, referral

api_router = APIRouter(prefix="/api/v1")
api_router.include_router(auth.router)
api_router.include_router(users.router)
api_router.include_router(chat.router)
api_router.include_router(admin.router)
api_router.include_router(system_settings.router)

# Orivory second-brain routes
api_router.include_router(memories.router)
api_router.include_router(entities.router)
api_router.include_router(entities.relations_router)  # /relations
api_router.include_router(entities.graph_router)   # /graph/snapshot, /graph/related/...
api_router.include_router(sources.router)

# Q2 Growth Track: Proactive Discovery Features
api_router.include_router(insights.router)      # /insights - Insight Cards
api_router.include_router(discovery.router)     # /discovery - Multi-hop Discovery
api_router.include_router(workspaces.router)    # /workspaces - Team Knowledge Base

# Onboarding & Demo
api_router.include_router(demo.router)         # /demo - Demo data for new users

# Analytics & Metrics
api_router.include_router(analytics.router)    # /analytics - Usage tracking

# Q4 User Acquisition: Referral System
api_router.include_router(referral.router)    # /referral - Viral referrals
