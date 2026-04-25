from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from fastapi.openapi.utils import get_openapi
from dotenv import load_dotenv
from database import Base, engine
from routes import auth, users, reviews, favorites

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
    print("Starting User / Reviewer Service...")
    yield
    print("Shutting down User / Reviewer Service...")

app = FastAPI(
    title="User / Reviewer Service",
    description="Authentication, user profile, favorites, and review operations for reviewers.",
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
        title="User / Reviewer Service",
        version="1.0.0",
        description="User auth, profile management, favorites, and reviewer-facing review endpoints.",
        routes=app.routes,
    )
    return app.openapi_schema

app.openapi = custom_openapi

app.include_router(auth.router)
app.include_router(users.router)
app.include_router(reviews.router)
app.include_router(favorites.router)

@app.get("/")
async def root():
    return {"service": "user-reviewer-service", "status": "ok"}

@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "user-reviewer-service"}