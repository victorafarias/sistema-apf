# app/main.py

from fastapi import FastAPI
from fastapi.responses import ORJSONResponse
from loguru import logger

# Importa o roteador que criamos
from app.routers import clientes

# Configuração do logger (pode manter como estava)
logger.add("logs/app.log", rotation="500 MB", retention="10 days", level="INFO")

app = FastAPI(
    title="Sistema de Gerenciamento de Contagens de Pontos de Função",
    version="0.1.0",
    default_response_class=ORJSONResponse,
)

# Inclui o roteador de clientes na aplicação principal
app.include_router(clientes.router)

@app.on_event("startup")
async def startup_event():
    logger.info("Iniciando a aplicação...")

@app.on_event("shutdown")
async def shutdown_event():
    logger.info("Encerrando a aplicação...")

@app.get("/", tags=["Root"])
def read_root():
    logger.info("Acessando a rota raiz.")
    return {"message": "Bem-vindo ao Sistema de Gerenciamento de APF!"}