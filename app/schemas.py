# app/schemas.py

from typing import Optional
from sqlmodel import SQLModel
from .models import TipoAjuste # <-- NOVO: Importa o Enum

# --- Schemas Cliente (existentes) ---
# ... (código existente, sem alteração)
class ClienteBase(SQLModel):
    nome: str

class ClienteCreate(ClienteBase):
    pass

class ClienteRead(ClienteBase):
    id: int

class ClienteUpdate(SQLModel):
    nome: Optional[str] = None

# --- NOVO: Schemas para Fator de Ajuste ---
class FatorAjusteBase(SQLModel):
    nome: str
    fator: float
    tipo_ajuste: TipoAjuste

class FatorAjusteCreate(FatorAjusteBase):
    pass

class FatorAjusteRead(FatorAjusteBase):
    id: int

class FatorAjusteUpdate(SQLModel):
    nome: Optional[str] = None
    fator: Optional[float] = None
    tipo_ajuste: Optional[TipoAjuste] = None