"""
Main FastAPI application for the ecommerce store.
"""
from fastapi import FastAPI
from .api import router

# Create FastAPI app
app = FastAPI(
    title="Ecommerce Store API",
    description="A complete ecommerce store API with cart management, checkout, and discount system",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)


# Include API routes
app.include_router(router, prefix="/api/v1")


@app.get("/", tags=["Root"])
async def root():
    """
    Root endpoint with API information.
    
    Returns:
        Basic API information and available endpoints
    """
    return {
        "message": "Ecommerce Store API",
        "version": "1.0.0",
        "docs": "/docs",
    }


@app.get("/health", tags=["Health"])
async def health_check():
    """
    Health check endpoint.
    
    Returns:
        Health status of the API
    """
    return {"status": "healthy", "service": "ecommerce-api"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

