# app/routers/contagens.py

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, Body
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession
from sqlalchemy.orm import selectinload
from fastapi import Form, Body, Request
from datetime import datetime, date, time

from app.database import get_session
from app.models import Contagem, Cliente, Projeto, Sistema, TipoContagemEnum, MetodoContagemEnum
from app.schemas import ContagemReadWithRelations, ContagemRead, ContagemUpdate, ContagemCreate

router = APIRouter(prefix="/contagens", tags=["Contagens"])

@router.post("/", response_model=ContagemRead, status_code=201)
async def create_contagem(
    payload: dict = Body(...),
    session: AsyncSession = Depends(get_session),
):
    # Campos obrigatórios
    required = ["descricao", "tipo_contagem", "metodo_contagem", "responsavel", "cliente_id", "projeto_id"]
    missing = [k for k in required if payload.get(k) in (None, "")]
    if missing:
        raise HTTPException(status_code=400, detail=f"Campos obrigatórios ausentes: {', '.join(missing)}")

    try:
        data = dict(
            descricao=payload["descricao"],
            tipo_contagem=TipoContagemEnum(payload["tipo_contagem"]),
            metodo_contagem=MetodoContagemEnum(payload["metodo_contagem"]),
            responsavel=payload["responsavel"],
            cliente_id=int(payload["cliente_id"]),
            projeto_id=int(payload["projeto_id"]),
            sistema_id=int(payload["sistema_id"]) if payload.get("sistema_id") else None,
        )

        # data_criacao opcional (YYYY-MM-DD ou ISO)
        if payload.get("data_criacao"):
            dc = payload["data_criacao"]
            if "T" in dc:
                data_criacao = datetime.fromisoformat(dc)
            else:
                data_criacao = datetime.combine(date.fromisoformat(dc), time.min)
        else:
            data_criacao = None

    except (ValueError, KeyError) as e:
        raise HTTPException(status_code=422, detail=f"Payload inválido: {e}")

    obj = Contagem(**data)
    if data_criacao:
        obj.data_criacao = data_criacao

    session.add(obj)
    await session.commit()
    await session.refresh(obj)
    return obj

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
            selectinload(Contagem.cliente),
            selectinload(Contagem.sistema),
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

@router.get("/{contagem_id}", response_model=ContagemReadWithRelations)
async def read_contagem(*, session: AsyncSession = Depends(get_session), contagem_id: int):
    """
    Busca uma contagem específica pelo seu ID, incluindo dados relacionados.
    """
    query = (
        select(Contagem)
        .where(Contagem.id == contagem_id)
        .options(
            selectinload(Contagem.projeto).selectinload(Projeto.cliente),
            selectinload(Contagem.sistema),
            selectinload(Contagem.cliente),
        )
    )
    result = await session.execute(query)
    contagem = result.scalar_one_or_none()
    if not contagem:
        raise HTTPException(status_code=404, detail="Contagem não encontrada")
    return contagem

@router.patch("/{contagem_id}", response_model=ContagemRead)
async def update_contagem(
    contagem_id: int,
    contagem_update: ContagemUpdate,
    session: AsyncSession = Depends(get_session),
):
    db_contagem = await session.get(Contagem, contagem_id)
    if not db_contagem:
        raise HTTPException(status_code=404, detail="Contagem não encontrada")

    update_data = contagem_update.model_dump(exclude_unset=True)

    # normaliza enums (podem chegar como string)
    if "tipo_contagem" in update_data:
        val = update_data["tipo_contagem"]
        if isinstance(val, str):
            update_data["tipo_contagem"] = TipoContagemEnum(val)
    if "metodo_contagem" in update_data:
        val = update_data["metodo_contagem"]
        if isinstance(val, str):
            update_data["metodo_contagem"] = MetodoContagemEnum(val)

    # normaliza data_criacao (date|string ISO -> datetime)
    if "data_criacao" in update_data:
        dc = update_data["data_criacao"]
        if isinstance(dc, str):
            update_data["data_criacao"] = (
                datetime.fromisoformat(dc)
                if "T" in dc
                else datetime.combine(date.fromisoformat(dc), time.min)
            )
        elif isinstance(dc, date) and not isinstance(dc, datetime):
            update_data["data_criacao"] = datetime.combine(dc, time.min)

    for k, v in update_data.items():
        setattr(db_contagem, k, v)

    await session.commit()
    await session.refresh(db_contagem)
    return db_contagem