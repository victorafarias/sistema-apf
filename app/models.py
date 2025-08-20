# app/models.py

import enum
from typing import Optional
from sqlmodel import Field, SQLModel

# --- Modelo Cliente (existente) ---
class Cliente(SQLModel, table=True):
    #... (código existente, sem alteração)
    id: Optional[int] = Field(default=None, primary_key=True)
    nome: str = Field(index=True, max_length=100)

# --- NOVO: Enum para o Tipo de Ajuste ---
class TipoAjuste(str, enum.Enum):
    PERCENTUAL = "Percentual"
    UNITARIO = "Unitário"

# --- NOVO: Modelo FatorAjuste ---
class FatorAjuste(SQLModel, table=True):
    """
    Representa a tabela 'fatorajuste' no banco de dados.
    """
    id: Optional[int] = Field(default=None, primary_key=True)
    nome: str = Field(index=True, max_length=100)
    fator: float
    tipo_ajuste: TipoAjuste