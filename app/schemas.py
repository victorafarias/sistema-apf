# app/schemas.py

from typing import Optional, List 
from datetime import datetime
from sqlmodel import SQLModel

from .models import TipoAjuste, Cliente, Projeto, FatorAjuste, TipoContagemEnum, MetodoContagemEnum, TipoFuncaoEnum


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

# --- NOVO: Schemas para Contagem ---
class ContagemBase(SQLModel):
    descricao: str
    tipo_contagem: TipoContagemEnum
    metodo_contagem: MetodoContagemEnum
    responsavel: str
    cliente_id: int
    projeto_id: int

class ContagemCreate(ContagemBase):
    pass

class ContagemRead(ContagemBase):
    id: int
    data_criacao: datetime

class ContagemUpdate(SQLModel):
    descricao: Optional[str] = None
    tipo_contagem: Optional[TipoContagemEnum] = None
    metodo_contagem: Optional[MetodoContagemEnum] = None
    responsavel: Optional[str] = None
    cliente_id: Optional[int] = None
    projeto_id: Optional[int] = None

class ContagemReadWithRelations(ContagemRead):
    cliente: ClienteRead
    projeto: ProjetoRead


# --- NOVO: Schemas para Funcao ---
class FuncaoBase(SQLModel):
    modulo: str
    funcionalidade: str
    nome: str
    tipo_funcao: TipoFuncaoEnum
    qtd_der: int
    qtd_rlr: int
    desc_der: Optional[str] = None
    desc_rlr: Optional[str] = None
    insumos: Optional[str] = None
    observacoes: Optional[str] = None
    contagem_id: int
    fator_ajuste_id: int

class FuncaoCreate(FuncaoBase):
    pass

class FuncaoRead(FuncaoBase):
    id: int

class FuncaoUpdate(SQLModel):
    modulo: Optional[str] = None
    funcionalidade: Optional[str] = None
    nome: Optional[str] = None
    tipo_funcao: Optional[TipoFuncaoEnum] = None
    qtd_der: Optional[int] = None
    qtd_rlr: Optional[int] = None
    desc_der: Optional[str] = None
    desc_rlr: Optional[str] = None
    insumos: Optional[str] = None
    observacoes: Optional[str] = None
    contagem_id: Optional[int] = None
    fator_ajuste_id: Optional[int] = None

class FuncaoReadWithRelations(FuncaoRead):
    contagem: ContagemRead
    fator_ajuste: FatorAjusteRead