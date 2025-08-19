# app/database.py

import os
from sqlmodel import create_engine
from dotenv import load_dotenv

# Carrega as variáveis de ambiente do arquivo .env
load_dotenv()

# Pega a URL do banco de dados a partir das variáveis de ambiente
DATABASE_URL = os.getenv("DATABASE_URL")

# Verifica se a URL do banco de dados foi definida
if not DATABASE_URL:
    raise ValueError("A variável de ambiente DATABASE_URL não foi definida!")

# Cria o "motor" (engine) do SQLModel, que o SQLModel usará para se comunicar com o banco.
# O `echo=True` é útil para desenvolvimento, pois imprime no console todas as queries SQL executadas.
# Em produção, você pode querer remover ou definir como `echo=False`.
engine = create_engine(DATABASE_URL, echo=True)