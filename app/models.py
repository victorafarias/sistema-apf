# app/models.py

import enum
from typing import Optional, List
from datetime import datetime
from sqlmodel import Field, SQLModel, Relationship
from sqlalchemy import (
    Column,
    Integer,
    String,
    ForeignKey,
    Date,
    Numeric,
    Text,
    DateTime
)


# --- Enums ---
class TipoAjuste(str, enum.Enum):
    PERCENTUAL = "Percentual"
    UNITARIO = "Unitário"

class TipoContagemEnum(str, enum.Enum):
    DESENVOLVIMENTO = "Desenvolvimento"
    MELHORIA = "Melhoria"
    APLICACAO = "Aplicação"

class MetodoContagemEnum(str, enum.Enum):
    DETALHADA = "Detalhada"
    ESTIMADA = "Estimada"
 
class TipoFuncaoEnum(str, enum.Enum):
    ALI = "ALI"
    AIE = "AIE"
    EE = "EE"
    CE = "CE"
    SE = "SE"
    INM = "INM"


# --- Modelos ---
class Cliente(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    nome: str = Field(index=True, max_length=100)
    
    projetos: List["Projeto"] = Relationship(back_populates="cliente")
    contagens: List["Contagem"] = Relationship(back_populates="cliente")


class FatorAjuste(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    nome: str = Field(index=True, max_length=100)
    fator: float
    tipo_ajuste: TipoAjuste

    funcoes: List["Funcao"] = Relationship(back_populates="fator_ajuste")


class Projeto(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    nome: str = Field(index=True, max_length=100)
    
    cliente_id: int = Field(foreign_key="cliente.id")
    cliente: Cliente = Relationship(back_populates="projetos")
    
    contagens: List["Contagem"] = Relationship(back_populates="projeto") 
    sistemas: List["Sistema"] = Relationship(back_populates="projeto")

class Contagem(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    descricao: str = Field(max_length=255)
    tipo_contagem: TipoContagemEnum
    metodo_contagem: MetodoContagemEnum
    
    data_criacao: datetime = Field(
        sa_column=Column(DateTime, default=datetime.utcnow, nullable=False)
    )

    responsavel: str = Field(max_length=100)
    
    cliente_id: int = Field(foreign_key="cliente.id")
    cliente: Cliente = Relationship(back_populates="contagens")
    
    projeto_id: int = Field(foreign_key="projeto.id")
    projeto: "Projeto" = Relationship(back_populates="contagens")
    sistema_id: Optional[int] = Field(default=None, foreign_key="sistema.id")
    sistema: Optional["Sistema"] = Relationship(back_populates="contagens") 
    
    funcoes: List["Funcao"] = Relationship(back_populates="contagem")


class Funcao(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    modulo: str = Field(max_length=100)
    funcionalidade: str = Field(max_length=255)
    nome: str = Field(index=True, max_length=255)
    tipo_funcao: TipoFuncaoEnum
    qtd_der: int
    qtd_rlr: int
    desc_der: Optional[str] = Field(default=None, sa_column=Column(Text))
    desc_rlr: Optional[str] = Field(default=None, sa_column=Column(Text))
    insumos: Optional[str] = Field(default=None, sa_column=Column(Text))
    observacoes: Optional[str] = Field(default=None, sa_column=Column(Text))
    
    contagem_id: int = Field(foreign_key="contagem.id")
    contagem: Contagem = Relationship(back_populates="funcoes")
    
    fator_ajuste_id: int = Field(foreign_key="fatorajuste.id")
    fator_ajuste: FatorAjuste = Relationship(back_populates="funcoes")

class Sistema(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    nome: str = Field(index=True, max_length=100)

    projeto_id: int = Field(foreign_key="projeto.id")
    projeto: Projeto = Relationship(back_populates="sistemas")
    contagens: List["Contagem"] = Relationship(back_populates="sistema")