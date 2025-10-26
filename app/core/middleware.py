import time
from typing import Callable, Awaitable

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from starlette.responses import Response


from app.core import logger


def add_middleware(app: FastAPI):
    """Attach custom middlewares to the FastAPI app."""

    @app.middleware("http")
    # This function is registered as middleware and does not need to be accessed directly.
    async def log_and_handle_errors(  # type: ignore
        request: Request, call_next: Callable[[Request], Awaitable[Response]]
    ) -> Response | JSONResponse:
        start_time = time.time()
        try:
            # Process the request
            response: Response = await call_next(request)

            # Add process time header
            process_time: float = time.time() - start_time
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
