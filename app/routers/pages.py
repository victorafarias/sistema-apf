# app/routers/pages.py

import httpx
from typing import Optional
from fastapi import APIRouter, Request, Depends, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from loguru import logger

router = APIRouter(tags=["Pages"])
templates = Jinja2Templates(directory="templates")

# URL base da nossa própria API
API_BASE_URL = "http://127.0.0.1:8000/api"

@router.get("/clientes", response_class=HTMLResponse)
async def list_clientes_page(
    request: Request, 
    nome_filter: Optional[str] = None, 
    id_filter: Optional[str] = None
): # <-- NOVO: Recebe os filtros da URL
    """
    Renderiza a página que lista os clientes, aplicando filtros.
    """
    logger.info("Acessando a página de listagem de clientes.")
    clientes = []
    
    # Constrói os parâmetros da query para a chamada da API
    params = {}
    if nome_filter:
        params["nome_filter"] = nome_filter
    if id_filter:
        params["id_filter"] = id_filter
    
    try:
        async with httpx.AsyncClient() as client:
            # ADICIONADO: Envia os parâmetros de filtro para a API
            response = await client.get(f"{API_BASE_URL}/clientes/", params=params)
        
        logger.debug(f"Página de listagem chamou API. Status: {response.status_code}")
        if response.status_code == 200:
            clientes = response.json()
            logger.info(f"Clientes encontrados via API: {len(clientes)}")
        else:
            logger.error(f"Erro ao buscar clientes da API. Resposta: {response.text}")

    except httpx.RequestError as exc:
        logger.critical(f"Erro de conexão ao tentar chamar a API de clientes: {exc}")

    # Renderiza o template, passando os filtros de volta para preencher os campos
    return templates.TemplateResponse("clientes_list.html", {
        "request": request,
        "clientes": clientes,
        "nome_filter": nome_filter,
        "id_filter": id_filter
    })

# app/routers/pages.py
# ... (adicionar ao final do arquivo)

@router.get("/clientes/novo", response_class=HTMLResponse)
async def create_cliente_form(request: Request):
    """
    Renderiza a página com o formulário para criar um novo cliente.
    """
    return templates.TemplateResponse("clientes_form.html", {"request": request})

@router.post("/clientes/novo", response_class=HTMLResponse)
async def handle_create_cliente(request: Request, nome: str = Form(...)):
    """
    Recebe os dados do formulário e chama a API para criar o cliente.
    """
    logger.info(f"Recebido formulário para criar cliente: {nome}")
    async with httpx.AsyncClient() as client:
        response = await client.post(f"{API_BASE_URL}/clientes/", json={"nome": nome})
    
    # --- LOGS DE DIAGNÓSTICO ---
    logger.debug(f"API respondeu com status: {response.status_code}")
    logger.debug(f"Conteúdo da resposta da API: {response.text}")
    # ---------------------------

    if response.status_code == 201:
        logger.info("Cliente criado com sucesso. Redirecionando para a lista.")
        return RedirectResponse(url="/clientes", status_code=303)
    else:
        logger.error("Falha ao criar cliente. API não retornou 201.")
        # Se deu erro, renderiza o formulário novamente com uma mensagem de erro
        return templates.TemplateResponse("clientes_form.html", {
            "request": request,
            "error": "Ocorreu um erro ao salvar o cliente. Verifique os logs."
        })
    
    # app/routers/pages.py (adicionar ao final do arquivo)

@router.get("/clientes/{cliente_id}/editar", response_class=HTMLResponse)
async def edit_cliente_form(request: Request, cliente_id: int):
    """
    Busca os dados de um cliente na API e renderiza o formulário de edição.
    """
    try:
        async with httpx.AsyncClient() as client:
            # Chama a API para obter os dados do cliente específico
            response = await client.get(f"{API_BASE_URL}/clientes/{cliente_id}")
        
        if response.status_code == 200:
            cliente = response.json()
            return templates.TemplateResponse("clientes_edit.html", {
                "request": request,
                "cliente": cliente
            })
        else:
            # Se o cliente não for encontrado, redireciona para a lista
            return RedirectResponse(url="/clientes", status_code=303)
    except httpx.RequestError as exc:
        logger.critical(f"Erro de conexão ao buscar cliente para edição: {exc}")
        return RedirectResponse(url="/clientes", status_code=303)

@router.post("/clientes/{cliente_id}/editar", response_class=HTMLResponse)
async def handle_edit_cliente(request: Request, cliente_id: int, nome: str = Form(...)):
    """
    Recebe os dados do formulário de edição e chama a API para atualizar o cliente.
    """
    try:
        async with httpx.AsyncClient() as client:
            # Chama o endpoint PATCH da API para atualizar parcialmente o cliente
            response = await client.patch(
                f"{API_BASE_URL}/clientes/{cliente_id}",
                json={"nome": nome}
            )
        
        if response.status_code == 200:
            # Se a atualização foi bem-sucedida, redireciona para a lista
            return RedirectResponse(url="/clientes", status_code=303)
        else:
            # Se deu erro, renderiza o formulário novamente com uma mensagem de erro
            error_msg = response.json().get("detail", "Erro desconhecido")
            return templates.TemplateResponse("clientes_edit.html", {
                "request": request,
                "cliente": {"id": cliente_id, "nome": nome},
                "error": f"Erro ao atualizar: {error_msg}"
            })
    except httpx.RequestError as exc:
        logger.critical(f"Erro de conexão ao editar cliente: {exc}")
        # Lógica de erro similar à anterior

# app/routers/pages.py (adicionar ao final do arquivo)

@router.get("/clientes/{cliente_id}/excluir", response_class=HTMLResponse)
async def delete_cliente_form(request: Request, cliente_id: int):
    """
    Mostra uma página de confirmação antes de excluir um cliente.
    """
    async with httpx.AsyncClient() as client:
        response = await client.get(f"{API_BASE_URL}/clientes/{cliente_id}")
    
    if response.status_code == 200:
        cliente = response.json()
        return templates.TemplateResponse("clientes_delete.html", {
            "request": request,
            "cliente": cliente
        })
    else:
        return RedirectResponse(url="/clientes", status_code=303)


@router.post("/clientes/{cliente_id}/excluir", response_class=HTMLResponse)
async def handle_delete_cliente(request: Request, cliente_id: int):
    """
    Chama a API para deletar o cliente e redireciona para a lista.
    """
    async with httpx.AsyncClient() as client:
        response = await client.delete(f"{API_BASE_URL}/clientes/{cliente_id}")
    
    # Após a exclusão, sempre redireciona para a lista de clientes
    return RedirectResponse(url="/clientes", status_code=303)