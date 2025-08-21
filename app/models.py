# app/models.py

import enum
from typing import Optional, List # Adicione List
from sqlmodel import Field, SQLModel, Relationship # Adicione Relationship

# --- Modelo Cliente (MODIFICADO) ---
class Cliente(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    nome: str = Field(index=True, max_length=100)
    
    # Adicionamos o relacionamento inverso: um Cliente pode ter vários Projetos.
    # O 'back_populates' diz ao SQLModel qual campo no modelo 'Projeto'
    # se refere de volta a este. Isso mantém os dois lados sincronizados.
    projetos: List["Projeto"] = Relationship(back_populates="cliente")


# --- Enum para o Tipo de Ajuste (sem alteração) ---
class TipoAjuste(str, enum.Enum):
    PERCENTUAL = "Percentual"
    UNITARIO = "Unitário"


# --- Modelo FatorAjuste (sem alteração) ---
class FatorAjuste(SQLModel, table=True):
    #... (código existente, sem alteração)
    id: Optional[int] = Field(default=None, primary_key=True)
    nome: str = Field(index=True, max_length=100)
    fator: float
    tipo_ajuste: TipoAjuste


# --- NOVO: Modelo Projeto ---
class Projeto(SQLModel, table=True):
    """
    Representa a tabela 'projeto' no banco de dados.
    """
    id: Optional[int] = Field(default=None, primary_key=True)
    nome: str = Field(index=True, max_length=100)
    
    # Chave estrangeira que aponta para o 'id' da tabela 'cliente'
    cliente_id: int = Field(foreign_key="cliente.id")
    
    # O relacionamento principal: um Projeto pertence a um Cliente.
    # O 'back_populates' aqui corresponde ao que definimos no modelo Cliente.
    cliente: Cliente = Relationship(back_populates="projetos")