# app/schemas.py

from typing import Optional
from sqlmodel import SQLModel
from .models import TipoAjuste, Cliente, Projeto

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

# --- NOVO: Schemas para Projeto ---

class ProjetoBase(SQLModel):
    nome: str
    cliente_id: int

class ProjetoCreate(ProjetoBase):
    pass

# Schema para exibir um projeto, mas sem os detalhes do cliente
class ProjetoRead(ProjetoBase):
    id: int

# Schema para atualizar, todos os campos são opcionais
class ProjetoUpdate(SQLModel):
    nome: Optional[str] = None
    cliente_id: Optional[int] = None

# Schema avançado para exibir um projeto JUNTO com os dados do cliente
# Isso é o que usaremos na nossa lista para ter todas as informações
class ProjetoReadWithCliente(ProjetoRead):
    cliente: ClienteRead