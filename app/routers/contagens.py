# app/routers/contagens.py

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession
from sqlalchemy.orm import selectinload

from app.database import get_session
from app.models import Contagem, Cliente, Projeto, Sistema, TipoContagemEnum, MetodoContagemEnum
from app.schemas import ContagemReadWithRelations

router = APIRouter(prefix="/contagens", tags=["Contagens"])

@router.get("/", response_model=List[ContagemReadWithRelations])
async def read_contagens(
    *,
    session: AsyncSession = Depends(get_session),
    sort: str = Query("-data_criacao"), # Ordenação padrão
    cliente_id: Optional[int] = Query(None),
    projeto_id: Optional[int] = Query(None),
    sistema_id: Optional[int] = Query(None),
    descricao: Optional[str] = Query(None),
    tipo_contagem: Optional[TipoContagemEnum] = Query(None),
    metodo_contagem: Optional[MetodoContagemEnum] = Query(None),
):
    """
    Lista as contagens com filtros avançados e ordenação.
    """
    query = (
        select(Contagem)
        .options(
            selectinload(Contagem.projeto).selectinload(Projeto.cliente),
            selectinload(Contagem.cliente), # Carrega o cliente diretamente também
        )
    )

    # Aplicação dos filtros
    if cliente_id:
        query = query.where(Contagem.cliente_id == cliente_id)
    if projeto_id:
        query = query.where(Contagem.projeto_id == projeto_id)
    # Futuramente, adicionaremos o filtro de sistema aqui, após o relacionamento ser criado.
    # if sistema_id:
    #     query = query.where(Contagem.sistema_id == sistema_id) # Descomentar quando o modelo for atualizado
    if descricao:
        query = query.where(Contagem.descricao.ilike(f"%{descricao}%"))
    if tipo_contagem:
        query = query.where(Contagem.tipo_contagem == tipo_contagem)
    if metodo_contagem:
        query = query.where(Contagem.metodo_contagem == metodo_contagem)

    # Lógica de Ordenação
    order_by_column = None
    if sort:
        is_desc = sort.startswith("-")
        column_name = sort[1:] if is_desc else sort

        if hasattr(Contagem, column_name):
            column = getattr(Contagem, column_name)
            order_by_column = column.desc() if is_desc else column.asc()
        elif column_name == "cliente":
            order_by_column = Cliente.nome.desc() if is_desc else Cliente.nome.asc()
            query = query.join(Cliente)
        elif column_name == "projeto":
             order_by_column = Projeto.nome.desc() if is_desc else Projeto.nome.asc()
             query = query.join(Projeto)


    if order_by_column is not None:
        query = query.order_by(order_by_column)


    result = await session.execute(query)
    contagens = result.scalars().all()
    return contagens