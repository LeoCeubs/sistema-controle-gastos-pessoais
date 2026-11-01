from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.database import init_db
from app.routers import categorias, resumo, transacoes

STATIC_DIR = Path(__file__).resolve().parent.parent / "static"


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    yield


app = FastAPI(
    title="Sistema de Controle de Gastos Pessoais",
    description=(
        "API REST local para cadastro, categorização, consulta e exportação "
        "de receitas e despesas. Todos os dados ficam no computador do usuário."
    ),
    version="0.1.0",
    lifespan=lifespan,
)


# RNF09: erro sempre em JSON {"erro": "..."} com status semântico.
# Sem este handler o FastAPI devolveria 422 + {"detail": [...]}, formato que a SDD não prevê.
@app.exception_handler(RequestValidationError)
async def erro_de_validacao(request: Request, exc: RequestValidationError):
    primeiro = exc.errors()[0]
    campo = ".".join(str(p) for p in primeiro["loc"][1:]) or "requisição"
    return JSONResponse(
        status_code=400, content={"erro": f"{campo}: {primeiro['msg']}"}
    )


@app.exception_handler(StarletteHTTPException)
async def erro_http(request: Request, exc: StarletteHTTPException):
    if exc.status_code == 204 or exc.detail is None:
        return JSONResponse(status_code=exc.status_code, content=None)
    return JSONResponse(status_code=exc.status_code, content={"erro": exc.detail})


app.include_router(categorias.router)
app.include_router(transacoes.router)
app.include_router(resumo.router)


@app.get("/health", tags=["Infraestrutura"])
def health():
    """Verificação simples de que a API está no ar."""
    return {"status": "ok"}


# RF08/RNF03: interface web servida pela própria aplicação em http://localhost:8000
app.mount("/", StaticFiles(directory=STATIC_DIR, html=True), name="static")
