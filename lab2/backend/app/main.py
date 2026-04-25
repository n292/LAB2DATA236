from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from app.api.routes.member_routes import router as member_router
from app.core.config import settings
from app.db.session import Base, engine
from app.utils.kafka_producer import close_kafka_producer, get_kafka_producer


@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(bind=engine)
    get_kafka_producer()
    yield
    close_kafka_producer()


app = FastAPI(title=settings.app_name, lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.client_origin, "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/uploads", StaticFiles(directory=settings.upload_path), name="uploads")


@app.get("/health")
def health_check():
    return {
        "success": True,
        "message": "Backend is healthy",
        "kafka_enabled": settings.kafka_enabled,
        "kafka_bootstrap_servers": settings.kafka_bootstrap_server_list,
        "kafka_topics": {
            "member_created": settings.kafka_member_created_topic,
            "member_updated": settings.kafka_member_updated_topic,
            "profile_viewed": settings.kafka_profile_viewed_topic,
        },
    }


app.include_router(member_router, prefix=settings.api_v1_prefix)