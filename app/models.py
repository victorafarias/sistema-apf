# app/models.py

from typing import Optional
from sqlmodel import Field, SQLModel

class Cliente(SQLModel, table=True):
    """
    Representa a tabela 'cliente' no banco de dados.
    """
    id: Optional[int] = Field(default=None, primary_key=True)
    
    # O campo 'nome' terá um índice de banco de dados (index=True).
    # Isso acelera MUITO as buscas (filtros) por nome, o que é crucial
    # para a performance em tabelas com muitos registros.
    nome: str = Field(index=True, max_length=100)

# Manteremos este arquivo para adicionar outros modelos no futuro.