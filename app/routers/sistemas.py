# app/routers/sistemas.py

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession
from sqlalchemy.orm import selectinload, Session
from app import models, schemas

from app.database import get_session
from app.models import Projeto, Sistema
from app.schemas import (
    SistemaCreate,
    SistemaRead,
    SistemaUpdate,
    SistemaReadWithProjeto,
    ProjetoRead
)

router = APIRouter(prefix="/sistemas", tags=["Sistemas"])


@router.post("/", response_model=SistemaRead, status_code=201)
async def create_sistema(*, session: AsyncSession = Depends(get_session), sistema: SistemaCreate):
    db_sistema = Sistema.model_validate(sistema)
    session.add(db_sistema)
    await session.commit()
    await session.refresh(db_sistema)
    return db_sistema


@router.get("/", response_model=List[SistemaReadWithProjeto])
async def read_sistemas(
    *,
    session: AsyncSession = Depends(get_session),
    nome_filter: Optional[str] = None,
    projeto_id_filter: Optional[int] = None
):
    query = select(Sistema).options(
        selectinload(Sistema.projeto).selectinload(Projeto.cliente)
    )

    if nome_filter:
        query = query.where(Sistema.nome.ilike(f"%{nome_filter}%"))
    if projeto_id_filter:
        query = query.where(Sistema.projeto_id == projeto_id_filter)

    query = query.order_by(Sistema.nome)
    result = await session.execute(query)
    sistemas = result.scalars().all()
    return sistemas


@router.get("/{sistema_id}", response_model=SistemaReadWithProjeto)
async def read_sistema(*, session: AsyncSession = Depends(get_session), sistema_id: int):
    query = (
        select(Sistema)
        .where(Sistema.id == sistema_id)
        .options(selectinload(Sistema.projeto).selectinload(Projeto.cliente))
    )
    result = await session.execute(query)
    sistema = result.scalar_one_or_none()
    if not sistema:
        raise HTTPException(status_code=404, detail="Sistema não encontrado")
    return sistema


@router.patch("/{sistema_id}", response_model=SistemaRead)
async def update_sistema(
    *,
    session: AsyncSession = Depends(get_session),
    sistema_id: int,
    sistema_update: SistemaUpdate,
):
    db_sistema = await session.get(Sistema, sistema_id)
    if not db_sistema:
        raise HTTPException(status_code=404, detail="Sistema não encontrado")
    update_data = sistema_update.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_sistema, key, value)
    session.add(db_sistema)
    await session.commit()
    await session.refresh(db_sistema)
    return db_sistema


@router.delete("/{sistema_id}", status_code=204)
async def delete_sistema(*, session: AsyncSession = Depends(get_session), sistema_id: int):
    db_sistema = await session.get(Sistema, sistema_id)
    if not db_sistema:
        raise HTTPException(status_code=404, detail="Sistema não encontrado")
    await session.delete(db_sistema)
    await session.commit()
    return

@router.get("/projeto/{projeto_id}", response_model=List[SistemaRead])
async def listar_por_projeto(projeto_id: int, session: AsyncSession = Depends(get_session)):
    result = await session.execute(
        select(Sistema).where(Sistema.projeto_id == projeto_id).order_by(Sistema.nome.asc())
    )
    return result.scalars().all()