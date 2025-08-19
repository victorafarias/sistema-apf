# app/main.py

from fastapi import FastAPI, Request
from fastapi.responses import ORJSONResponse, HTMLResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from loguru import logger

# Importa os roteadores da API e das páginas
from app.routers import clientes, pages # <-- ADICIONADO pages

# ... (configuração do logger) ...
logger.add("logs/app.log", rotation="500 MB", retention="10 days", level="DEBUG")


app = FastAPI(
    title="Sistema de Gerenciamento de Contagens de Pontos de Função",
    version="0.1.0",
    default_response_class=ORJSONResponse,
)

# --- CONFIGURAÇÃO DO FRONT-END ---
# Aponta para a pasta onde os templates HTML estão localizados
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")
# ---------------------------------


# Inclui os roteadores na aplicação principal
app.include_router(clientes.router, prefix="/api") # <-- ADICIONADO PREFIXO /api
app.include_router(pages.router) # <-- NOVO ROTEADOR DE PÁGINAS


@app.on_event("startup")
async def startup_event():
    logger.info("Iniciando a aplicação...")

@app.on_event("shutdown")
async def shutdown_event():
    logger.info("Encerrando a aplicação...")

# A rota raiz agora vai redirecionar para a nossa página de clientes
@app.get("/", tags=["Root"], response_class=HTMLResponse, include_in_schema=False)
async def read_root(request: Request):
    # Por enquanto, apenas para confirmar que funciona.
    # Vamos criar um template para a raiz depois.
    return templates.TemplateResponse("root.html", {"request": request})