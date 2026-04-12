from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.openapi.utils import get_openapi
from contextlib import asynccontextmanager
from database import Base, engine
from routes import auth, users, restaurants, reviews, favorites, ai_assistant
from dotenv import load_dotenv
import os

load_dotenv()

# Create all database tables
Base.metadata.create_all(bind=engine)

# CORS configuration
cors_origins = [
    "http://localhost:3000",
    "http://localhost:3001",
    "http://localhost:5173",
    "http://127.0.0.1:3000",
    "http://127.0.0.1:3001",
]

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    print("Starting Yelp Backend API...")
    yield
    # Shutdown
    print("Shutting down Yelp Backend API...")


app = FastAPI(
    title="LabPair-45 Eats API",
    description="FastAPI backend for LabPair-45 Eats with AI assistant for restaurant recommendations, search, reviews, favorites, and user preferences management",
    version="1.0.0",
    lifespan=lifespan,
    openapi_url="/api/openapi.json",
    docs_url="/api/docs",
    redoc_url="/api/redoc"
)

# Add CORS middleware FIRST - before routes are registered
app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Custom OpenAPI schema
def custom_openapi():
    if app.openapi_schema:
        return app.openapi_schema
    
    openapi_schema = get_openapi(
        title="Yelp Prototype API",
        version="1.0.0",
        description="""
            Complete REST API for Yelp prototype featuring:
            - User authentication with JWT tokens
            - Restaurant search and management
            - Review system with ratings
            - Favorites management
            - AI Assistant for restaurant recommendations
            - User preferences management
            
            All endpoints require authentication except /auth/signup and /auth/login.
        """,
        routes=app.routes,
    )
    
    openapi_schema["info"]["x-logo"] = {
        "url": "https://fastapi.tiangolo.com/img/logo-margin/logo-teal.png"
    }
    
    app.openapi_schema = openapi_schema
    return app.openapi_schema

app.openapi = custom_openapi

# Include routers
app.include_router(auth.router)
app.include_router(users.router)
app.include_router(restaurants.router)
app.include_router(reviews.router)
app.include_router(favorites.router)
app.include_router(ai_assistant.router)


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "message": "Yelp Prototype API",
        "version": "1.0.0",
        "docs": "/docs"
    }


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )
