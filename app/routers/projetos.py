# app/routers/projetos.py

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession
from sqlalchemy.orm import selectinload # Import para otimizar a query

from app.database import get_session
from app.models import Projeto
from app.schemas import ProjetoCreate, ProjetoRead, ProjetoUpdate, ProjetoReadWithCliente

router = APIRouter(prefix="/projetos", tags=["Projetos"])

@router.post("/", response_model=ProjetoRead, status_code=201)
async def create_projeto(*, session: AsyncSession = Depends(get_session), projeto: ProjetoCreate):
    db_projeto = Projeto.model_validate(projeto)
    session.add(db_projeto)
    await session.commit()
    await session.refresh(db_projeto)
    return db_projeto

@router.get("/", response_model=List[ProjetoReadWithCliente])
async def read_projetos(
    *, 
    session: AsyncSession = Depends(get_session),
    nome_filter: Optional[str] = None, # <-- NOVO
    cliente_id_filter: Optional[int] = None # <-- NOVO
):
    """
    Lista os projetos com filtros por nome e cliente.
    """
    query = select(Projeto).options(selectinload(Projeto.cliente))

    if nome_filter:
        # Busca inteligente para o nome (case-insensitive e parcial)
        query = query.where(Projeto.nome.ilike(f"%{nome_filter}%"))

    if cliente_id_filter:
        # Filtro exato pelo ID do cliente
        query = query.where(Projeto.cliente_id == cliente_id_filter)

    query = query.order_by(Projeto.nome)
    
    result = await session.execute(query)
    projetos = result.scalars().all()
    return projetos

@router.get("/{projeto_id}", response_model=ProjetoReadWithCliente)
async def read_projeto(*, session: AsyncSession = Depends(get_session), projeto_id: int):
    query = select(Projeto).where(Projeto.id == projeto_id).options(selectinload(Projeto.cliente))
    result = await session.execute(query)
    projeto = result.scalar_one_or_none()
    if not projeto:
        raise HTTPException(status_code=404, detail="Projeto não encontrado")
    return projeto

@router.patch("/{projeto_id}", response_model=ProjetoRead)
async def update_projeto(*, session: AsyncSession = Depends(get_session), projeto_id: int, projeto_update: ProjetoUpdate):
    db_projeto = await session.get(Projeto, projeto_id)
    if not db_projeto:
        raise HTTPException(status_code=404, detail="Projeto não encontrado")
    update_data = projeto_update.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_projeto, key, value)
    session.add(db_projeto)
    await session.commit()
    await session.refresh(db_projeto)
    return db_projeto

@router.delete("/{projeto_id}", status_code=204)
async def delete_projeto(*, session: AsyncSession = Depends(get_session), projeto_id: int):
    db_projeto = await session.get(Projeto, projeto_id)
    if not db_projeto:
        raise HTTPException(status_code=404, detail="Projeto não encontrado")
    await session.delete(db_projeto)
    await session.commit()
    return