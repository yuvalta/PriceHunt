from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .api.routes import router
from .config.settings import get_settings
from .core.middleware import LoggingMiddleware
from .core.exceptions import AppException

settings = get_settings()

app = FastAPI(
    title="PriceHunt",
    description="Your AI-powered shopping assistant that finds better deals on AliExpress. Send a product link or search query to discover cheaper alternatives!",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add logging middleware
app.add_middleware(LoggingMiddleware)

# Include routers
app.include_router(router)

@app.exception_handler(AppException)
async def app_exception_handler(request, exc):
    return {
        "status": "error",
        "message": exc.message,
        "status_code": exc.status_code
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG
    ) 