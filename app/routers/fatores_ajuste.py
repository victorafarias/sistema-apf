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
    # Os filtros agora recebem strings para tratar entradas vazias antes da validação
    nome_filter: Optional[str] = Query(default=None),
    fator_filter: Optional[str] = Query(default=None),
    tipo_ajuste_filter: Optional[str] = Query(default=None),
):
    """
    Lista os fatores de ajuste com paginação e filtros robustos, ordenados por nome.
    """
    query = select(FatorAjuste)

    # Filtro por nome: ignora strings vazias ou com apenas espaços
    if nome_filter and nome_filter.strip():
        query = query.where(FatorAjuste.nome.ilike(f"%{nome_filter.strip()}%"))

    # Filtro por fator: Converte para float e ignora se inválido/vazio
    if fator_filter and fator_filter.strip():
        try:
            fator_value = float(fator_filter)
            query = query.where(FatorAjuste.fator == fator_value)
        except (ValueError, TypeError):
            # Se o valor não for um número válido (ex: string vazia), ignora o filtro
            pass

    # Filtro por tipo de ajuste: Converte para o Enum e ignora se inválido/vazio
    if tipo_ajuste_filter and tipo_ajuste_filter.strip():
        try:
            tipo_ajuste_value = TipoAjuste(tipo_ajuste_filter)
            query = query.where(FatorAjuste.tipo_ajuste == tipo_ajuste_value)
        except ValueError:
            # Se o valor não for um membro do Enum válido (ex: string vazia), ignora o filtro
            pass

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