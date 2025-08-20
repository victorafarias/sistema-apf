# app/routers/fatores_ajuste.py

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from app.database import get_session
from app.models import FatorAjuste, TipoAjuste
from app.schemas import FatorAjusteCreate, FatorAjusteRead, FatorAjusteUpdate

router = APIRouter(prefix="/fatores-ajuste", tags=["Fatores de Ajuste"])

@router.post("/", response_model=FatorAjusteRead, status_code=201)
async def create_fator_ajuste(
    *, session: AsyncSession = Depends(get_session), fator_ajuste: FatorAjusteCreate
):
    db_fator_ajuste = FatorAjuste.model_validate(fator_ajuste)
    session.add(db_fator_ajuste)
    await session.commit()
    await session.refresh(db_fator_ajuste)
    return db_fator_ajuste

@router.get("/", response_model=List[FatorAjusteRead])
async def read_fatores_ajuste(
    *,
    session: AsyncSession = Depends(get_session),
    offset: int = 0,
    limit: int = Query(default=100, lte=100),
    nome_filter: Optional[str] = None,
    fator_filter: Optional[float] = None, # <-- NOVO: Filtro para o fator
    tipo_ajuste_filter: Optional[TipoAjuste] = None # <-- NOVO: Filtro para o tipo
):
    """
    Lista os fatores de ajuste com paginação e filtros, ordenados por nome.
    """
    query = select(FatorAjuste)
    
    if nome_filter:
        # Busca inteligente para o nome (case-insensitive e parcial)
        query = query.where(FatorAjuste.nome.ilike(f"%{nome_filter}%"))
        
    if fator_filter is not None: # <-- NOVO: Lógica para o filtro de fator
        query = query.where(FatorAjuste.fator == fator_filter)
        
    if tipo_ajuste_filter: # <-- NOVO: Lógica para o filtro de tipo
        query = query.where(FatorAjuste.tipo_ajuste == tipo_ajuste_filter)
        
    query = query.order_by(FatorAjuste.nome).offset(offset).limit(limit)
    
    result = await session.execute(query)
    fatores = result.scalars().all()
    
    return fatores

@router.get("/{fator_id}", response_model=FatorAjusteRead)
async def read_fator_ajuste(*, session: AsyncSession = Depends(get_session), fator_id: int):
    fator = await session.get(FatorAjuste, fator_id)
    if not fator:
        raise HTTPException(status_code=404, detail="Fator de ajuste não encontrado")
    return fator

@router.patch("/{fator_id}", response_model=FatorAjusteRead)
async def update_fator_ajuste(
    *,
    session: AsyncSession = Depends(get_session),
    fator_id: int,
    fator_update: FatorAjusteUpdate,
):
    db_fator = await session.get(FatorAjuste, fator_id)
    if not db_fator:
        raise HTTPException(status_code=404, detail="Fator de ajuste não encontrado")
    update_data = fator_update.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_fator, key, value)
    session.add(db_fator)
    await session.commit()
    await session.refresh(db_fator)
    return db_fator

@router.delete("/{fator_id}", status_code=204)
async def delete_fator_ajuste(*, session: AsyncSession = Depends(get_session), fator_id: int):
    db_fator = await session.get(FatorAjuste, fator_id)
    if not db_fator:
        raise HTTPException(status_code=404, detail="Fator de ajuste não encontrado")
    await session.delete(db_fator)
    await session.commit()
    return