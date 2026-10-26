from fastapi import BackgroundTasks, FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from sqlalchemy.exc import SQLAlchemyError

from app.api.import_files import router as import_router
from app.api.routes import router
from app.infrastructure.outbox import dispatch_safely

app = FastAPI(title="AC Actions Map — AC Social", version="0.1.0")
app.include_router(router)
app.include_router(import_router)


@app.middleware("http")
async def private_responses(request: Request, call_next):
    size = request.headers.get("content-length", "")
    if size and (not size.isdigit() or int(size) > 1_048_576):
        return JSONResponse({"detail": "Requisição excede o limite permitido."}, status_code=413)
    # Limita também corpos chunked; não registra corpo, cookies ou query string.
    if request.method in {"POST", "PATCH", "PUT", "DELETE"}:
        total = 0
        chunks = []
        async for chunk in request.stream():
            total += len(chunk)
            if total > 1_048_576:
                return JSONResponse(
                    {"detail": "Requisição excede o limite permitido."}, status_code=413
                )
            chunks.append(chunk)
        request._body = b"".join(chunks)
    response = await call_next(request)
    if (
        request.method in {"POST", "PATCH", "PUT", "DELETE"}
        and response.status_code < 300
        and request.url.path.startswith(("/api/v1/acoes", "/api/v1/importacoes"))
    ):
        tasks = BackgroundTasks()
        if response.background:
            tasks.add_task(response.background)
        tasks.add_task(dispatch_safely)
        response.background = tasks
    response.headers["Cache-Control"] = "no-store"
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["Referrer-Policy"] = "no-referrer"
    return response


@app.exception_handler(RequestValidationError)
async def validation_error(_request: Request, error: RequestValidationError):
    return JSONResponse(
        status_code=422,
        content={
            "detail": "Confira os campos informados.",
            "campos": [
                {"campo": ".".join(str(p) for p in item["loc"]), "mensagem": item["msg"]}
                for item in error.errors()
            ],
        },
    )


@app.exception_handler(SQLAlchemyError)
async def database_error(_request: Request, _error: SQLAlchemyError):
    return JSONResponse(
        status_code=503, content={"detail": "Não foi possível consultar os dados. Tente novamente."}
    )


@app.exception_handler(Exception)
async def unexpected_error(_request: Request, _error: Exception):
    return JSONResponse(
        status_code=503,
        content={"detail": "Serviço temporariamente indisponível. Procure a equipe de Tecnologia."},
    )
