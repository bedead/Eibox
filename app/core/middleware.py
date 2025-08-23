import time
from app.core.logging import logger
from fastapi import Request
from fastapi.responses import JSONResponse


def add_middleware(app):
    """Attach custom middlewares to the FastAPI app."""

    @app.middleware("http")
    async def log_and_handle_errors(request: Request, call_next):
        start_time = time.time()
        try:
            # Process the request
            response = await call_next(request)

            # Add process time header
            process_time = time.time() - start_time
            response.headers["X-Process-Time"] = f"{process_time:.4f}s"
            logger.debug(
                f"✅ {request.method} {request.url.path} [{response.status_code}] in {process_time:.4f}s"
            )
            return response

        except Exception as e:
            # Handle unexpected errors gracefully
            logger.exception(f"❌ Error processing request: {e}")
            return JSONResponse(
                status_code=500,
                content={"detail": "Internal Server Error"},
            )
