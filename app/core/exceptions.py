import structlog
from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

logger = structlog.get_logger()

class FarmingException(Exception):
    def __init__(self, status_code: int, error_code: str, message: str):
        self.status_code = status_code
        self.error_code = error_code
        self.message = message

def setup_exception_handlers(app: FastAPI):

    @app.exception_handler(FarmingException)
    async def farming_exception_handler(request: Request, exc: FarmingException):
        logger.error(
            "Farming exception occurred",
            error_code=exc.error_code,
            message=exc.message,
            status_code=exc.status_code,
            request_id=getattr(request.state, 'request_id', None)
        )
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "success": False,
                "error_code": exc.error_code,
                "message": exc.message,
                "request_id": getattr(request.state, 'request_id', None)
            }
        )

    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(request: Request, exc: RequestValidationError):
        logger.error(
            "Validation error",
            errors=exc.errors(),
            request_id=getattr(request.state, 'request_id', None)
        )
        return JSONResponse(
            status_code=422,
            content={
                "success": False,
                "error_code": "VALIDATION_ERROR",
                "message": "Invalid input data",
                "details": exc.errors(),
                "request_id": getattr(request.state, 'request_id', None)
            }
        )

    @app.exception_handler(HTTPException)
    async def http_exception_handler(request: Request, exc: HTTPException):
        logger.error(
            "HTTP exception",
            status_code=exc.status_code,
            detail=exc.detail,
            request_id=getattr(request.state, 'request_id', None)
        )
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "success": False,
                "error_code": "HTTP_ERROR",
                "message": exc.detail,
                "request_id": getattr(request.state, 'request_id', None)
            }
        )

    @app.exception_handler(Exception)
    async def general_exception_handler(request: Request, exc: Exception):
        logger.error(
            "Unexpected error",
            error=str(exc),
            error_type=type(exc).__name__,
            request_id=getattr(request.state, 'request_id', None)
        )
        return JSONResponse(
            status_code=500,
            content={
                "success": False,
                "error_code": "INTERNAL_ERROR",
                "message": "An unexpected error occurred",
                "request_id": getattr(request.state, 'request_id', None)
            }
        )
