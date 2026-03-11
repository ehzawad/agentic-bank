import logging

from anthropic import APIError
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from chatbot.api.routes import router

logger = logging.getLogger(__name__)


def create_app() -> FastAPI:
    app = FastAPI(
        title="B2B Banking Chatbot",
        description="Product-grade B2B chatbot powered by Claude Sonnet 4.6",
        version="0.1.0",
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(router)

    @app.exception_handler(APIError)
    async def anthropic_api_error_handler(request: Request, exc: APIError) -> JSONResponse:
        logger.error(f"Anthropic API error: {exc}")
        return JSONResponse(
            status_code=502,
            content={"detail": "AI service is temporarily unavailable. Please try again."},
        )

    @app.exception_handler(Exception)
    async def generic_exception_handler(request: Request, exc: Exception) -> JSONResponse:
        logger.error(f"Unhandled exception: {exc}", exc_info=True)
        return JSONResponse(
            status_code=500,
            content={"detail": "Internal server error"},
        )

    return app


app = create_app()
