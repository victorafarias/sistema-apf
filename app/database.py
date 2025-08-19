# app/database.py

import os
from sqlmodel.ext.asyncio.session import AsyncEngine, AsyncSession
from sqlmodel import SQLModel, create_engine
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv

# Carrega as variáveis de ambiente do arquivo .env
load_dotenv()

# Pega a URL do banco de dados a partir das variáveis de ambiente
DATABASE_URL = os.getenv("DATABASE_URL")

# Verifica se a URL do banco de dados foi definida
if not DATABASE_URL:
    raise ValueError("A variável de ambiente DATABASE_URL não foi definida!")

# Modificamos a string de conexão para usar o driver asyncpg
async_database_url = DATABASE_URL.replace("postgresql://", "postgresql+asyncpg://")

# Criamos o "motor" assíncrono.
# O `echo=True` continua útil para ver as queries SQL durante o desenvolvimento.
async_engine = create_async_engine(async_database_url, echo=True, future=True)


async def get_session() -> AsyncSession:
    """
    Função de dependência que cria e fornece uma sessão de banco de dados por requisição.
    """
    async_session = sessionmaker(
        bind=async_engine, class_=AsyncSession, expire_on_commit=False
    )
    async with async_session() as session:
        yield session