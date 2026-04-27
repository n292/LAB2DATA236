from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from fastapi.openapi.utils import get_openapi
from dotenv import load_dotenv
from routes import auth, restaurants

load_dotenv()

cors_origins = [
    "http://localhost:3000",
    "http://localhost:3001",
    "http://localhost:5173",
    "http://127.0.0.1:3000",
    "http://127.0.0.1:3001",
]

@asynccontextmanager
async def lifespan(app: FastAPI):
    print("Starting Restaurant Owner Service...")
    yield
    print("Shutting down Restaurant Owner Service...")

app = FastAPI(
    title="Restaurant Owner Service",
    description="Owner-facing restaurant management operations.",
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
        title="Restaurant Owner Service",
        version="1.0.0",
        description="Restaurant owner authentication and owner-facing restaurant routes.",
        routes=app.routes,
    )
    return app.openapi_schema

app.openapi = custom_openapi

app.include_router(auth.router)
app.include_router(restaurants.router)

@app.get("/")
async def root():
    return {"service": "owner-service", "status": "ok"}

@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "owner-service"}