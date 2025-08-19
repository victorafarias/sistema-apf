# app/routers/clientes.py

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from app.database import get_session
from app.models import Cliente
from app.schemas import ClienteCreate, ClienteRead, ClienteUpdate

# Cria um novo roteador com um prefixo e tags para organização na documentação
router = APIRouter(prefix="/clientes", tags=["Clientes"])

@router.post("/", response_model=ClienteRead, status_code=201)
async def create_cliente(
    *, 
    session: AsyncSession = Depends(get_session), 
    cliente: ClienteCreate
):
    """
    Cria um novo cliente no banco de dados.
    """
    # Cria uma instância do modelo do banco a partir do schema recebido
    db_cliente = Cliente.model_validate(cliente)
    
    session.add(db_cliente)
    await session.commit()
    await session.refresh(db_cliente)
    
    return db_cliente


@router.get("/", response_model=List[ClienteRead])
async def read_clientes(
    *,
    session: AsyncSession = Depends(get_session),
    offset: int = 0,
    limit: int = Query(default=100, lte=100),
    nome_filter: Optional[str] = None,
    id_filter: Optional[int] = None # <-- NOVO: Parâmetro para filtrar por ID
):
    """
    Lista os clientes com paginação e filtros, ordenados por nome.
    """
    query = select(Cliente)
    
    if nome_filter:
    # Usa 'ilike' para buscar por partes do nome, ignorando maiúsculas/minúsculas.
    # O f-string com '%' adiciona os curingas para a busca em qualquer parte do texto.
        query = query.where(Cliente.nome.ilike(f"%{nome_filter}%"))
        
    if id_filter: # <-- NOVO: Lógica para aplicar o filtro de ID
        query = query.where(Cliente.id == id_filter)
        
    # ADICIONADO: Ordena a consulta pelo nome do cliente em ordem crescente
    query = query.order_by(Cliente.nome)
    
    query = query.offset(offset).limit(limit)
    
    result = await session.execute(query)
    clientes = result.scalars().all()
    
    return clientes


@router.get("/{cliente_id}", response_model=ClienteRead)
async def read_cliente(
    *, 
    session: AsyncSession = Depends(get_session), 
    cliente_id: int
):
    """
    Busca um único cliente pelo seu ID.
    """
    cliente = await session.get(Cliente, cliente_id)
    if not cliente:
        raise HTTPException(status_code=404, detail="Cliente não encontrado")
    return cliente


@router.patch("/{cliente_id}", response_model=ClienteRead)
async def update_cliente(
    *,
    session: AsyncSession = Depends(get_session),
    cliente_id: int,
    cliente_update: ClienteUpdate,
):
    """
    Atualiza um cliente existente. Usa PATCH para permitir atualizações parciais.
    """
    db_cliente = await session.get(Cliente, cliente_id)
    if not db_cliente:
        raise HTTPException(status_code=404, detail="Cliente não encontrado")

    # Pega os dados do schema de atualização, excluindo o que não foi enviado
    update_data = cliente_update.model_dump(exclude_unset=True)
    
    # Atualiza os campos do objeto do banco com os novos dados
    for key, value in update_data.items():
        setattr(db_cliente, key, value)
        
    session.add(db_cliente)
    await session.commit()
    await session.refresh(db_cliente)
    
    return db_cliente


@router.delete("/{cliente_id}", status_code=204)
async def delete_cliente(
    *, 
    session: AsyncSession = Depends(get_session), 
    cliente_id: int
):
    """
    Deleta um cliente.
    """
    db_cliente = await session.get(Cliente, cliente_id)
    if not db_cliente:
        raise HTTPException(status_code=404, detail="Cliente não encontrado")
        
    await session.delete(db_cliente)
    await session.commit()
    
    # Retorna uma resposta 204 No Content, que é o padrão para deletes bem-sucedidos
    return