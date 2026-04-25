from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from fastapi.openapi.utils import get_openapi
from dotenv import load_dotenv
from database import Base, engine
from routes import reviews

try:
    from app.review_kafka_routes import router as review_kafka_router
except ImportError:
    from review_kafka_routes import router as review_kafka_router


load_dotenv()
Base.metadata.create_all(bind=engine)

cors_origins = [
    "http://localhost:3000",
    "http://localhost:3001",
    "http://localhost:5173",
    "http://127.0.0.1:3000",
    "http://127.0.0.1:3001",
]


@asynccontextmanager
async def lifespan(app: FastAPI):
    print("Starting Review Service...")
    yield
    print("Shutting down Review Service...")


app = FastAPI(
    title="Review Service",
    description="Review CRUD and review retrieval operations.",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def custom_openapi():
    if app.openapi_schema:
        return app.openapi_schema

    app.openapi_schema = get_openapi(
        title="Review Service",
        version="1.0.0",
        description="Review creation, update, delete, and lookup endpoints.",
        routes=app.routes,
    )
    return app.openapi_schema


app.openapi = custom_openapi


app.include_router(reviews.router)


app.include_router(review_kafka_router)


@app.get("/")
async def root():
    return {"service": "review-service", "status": "ok"}


@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "review-service"}