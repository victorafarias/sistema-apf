# app/schemas.py

from typing import Optional
from sqlmodel import SQLModel

# Schema base com os campos comuns
class ClienteBase(SQLModel):
    nome: str

# Schema para criação de um cliente (o que a API recebe no POST)
class ClienteCreate(ClienteBase):
    pass

# Schema para leitura de um cliente (o que a API retorna no GET)
# Inclui o 'id' que é gerado pelo banco.
class ClienteRead(ClienteBase):
    id: int

# Schema para atualização de um cliente (o que a API recebe no PATCH)
# Todos os campos são opcionais para permitir atualizações parciais.
class ClienteUpdate(SQLModel):
    nome: Optional[str] = None