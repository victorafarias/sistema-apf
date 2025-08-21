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
    clientefs = []
    
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
    return templates.TemplateResponse("clientes/list.html", {
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
    return templates.TemplateResponse("clientes/form.html", {"request": request})

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
        return templates.TemplateResponse("clientes/form.html", {
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
            return templates.TemplateResponse("clientes/edit.html", {
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
            return templates.TemplateResponse("clientes/edit.html", {
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
        return templates.TemplateResponse("clientes/delete.html", {
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

# app/routers/pages.py (adicionar ao final do arquivo)
from app.models import TipoAjuste # Importa o Enum para usar no formulário

# --- ROTAS PARA FATORES DE AJUSTE ---

@router.get("/fatores-ajuste", response_class=HTMLResponse)
async def list_fatores_page(
    request: Request, 
    nome_filter: Optional[str] = None,
    fator_filter: Optional[str] = None, # <-- NOVO
    tipo_ajuste_filter: Optional[str] = None # <-- NOVO (como string para pegar o valor vazio)
):
    """
    Renderiza a página que lista os fatores de ajuste, aplicando filtros.
    """
    params = {}
    if nome_filter:
        params["nome_filter"] = nome_filter
    if fator_filter is not None:
        params["fator_filter"] = fator_filter
    if tipo_ajuste_filter:
        params["tipo_ajuste_filter"] = tipo_ajuste_filter

    async with httpx.AsyncClient() as client:
        response = await client.get(f"{API_BASE_URL}/fatores-ajuste/", params=params)

    fatores = response.json() if response.status_code == 200 else []

    return templates.TemplateResponse("fatores_ajuste/list.html", {
        "request": request,
        "fatores": fatores,
        "nome_filter": nome_filter,
        "fator_filter": fator_filter, # <-- NOVO
        "tipo_ajuste_filter": tipo_ajuste_filter, # <-- NOVO
        "tipos_ajuste": [e.value for e in TipoAjuste] # <-- NOVO (para o combo)
    })

@router.get("/fatores-ajuste/novo", response_class=HTMLResponse)
async def create_fator_form(request: Request):
    return templates.TemplateResponse("fatores_ajuste/form.html", {
        "request": request,
        "tipos_ajuste": [e.value for e in TipoAjuste] # Passa os valores do Enum para o template
    })

@router.post("/fatores-ajuste/novo", response_class=HTMLResponse)
async def handle_create_fator(
    request: Request,
    nome: str = Form(...),
    fator: float = Form(...),
    tipo_ajuste: TipoAjuste = Form(...)
):
    payload = {"nome": nome, "fator": fator, "tipo_ajuste": tipo_ajuste.value}
    async with httpx.AsyncClient() as client:
        response = await client.post(f"{API_BASE_URL}/fatores-ajuste/", json=payload)
    if response.status_code == 201:
        return RedirectResponse(url="/fatores-ajuste", status_code=303)
    else:
        return templates.TemplateResponse("fatores_ajuste/form.html", {
            "request": request,
            "tipos_ajuste": [e.value for e in TipoAjuste],
            "error": "Erro ao salvar o fator de ajuste."
        })

@router.get("/fatores-ajuste/{fator_id}/editar", response_class=HTMLResponse)
async def edit_fator_form(request: Request, fator_id: int):
    async with httpx.AsyncClient() as client:
        response = await client.get(f"{API_BASE_URL}/fatores-ajuste/{fator_id}")
    if response.status_code == 200:
        fator = response.json()
        return templates.TemplateResponse("fatores_ajuste/edit.html", {
            "request": request,
            "fator": fator,
            "tipos_ajuste": [e.value for e in TipoAjuste]
        })
    return RedirectResponse(url="/fatores-ajuste", status_code=303)

@router.post("/fatores-ajuste/{fator_id}/editar", response_class=HTMLResponse)
async def handle_edit_fator(
    request: Request,
    fator_id: int,
    nome: str = Form(...),
    fator: float = Form(...),
    tipo_ajuste: TipoAjuste = Form(...)
):
    payload = {"nome": nome, "fator": fator, "tipo_ajuste": tipo_ajuste.value}
    async with httpx.AsyncClient() as client:
        response = await client.patch(f"{API_BASE_URL}/fatores-ajuste/{fator_id}", json=payload)
    if response.status_code == 200:
        return RedirectResponse(url="/fatores-ajuste", status_code=303)
    # Lógica de erro...
    return RedirectResponse(url=f"/fatores-ajuste/{fator_id}/editar", status_code=303)


@router.get("/fatores-ajuste/{fator_id}/excluir", response_class=HTMLResponse)
async def delete_fator_form(request: Request, fator_id: int):
    async with httpx.AsyncClient() as client:
        response = await client.get(f"{API_BASE_URL}/fatores-ajuste/{fator_id}")
    if response.status_code == 200:
        fator = response.json()
        return templates.TemplateResponse("fatores_ajuste/delete.html", {
            "request": request,
            "fator": fator
        })
    return RedirectResponse(url="/fatores-ajuste", status_code=303)

@router.post("/fatores-ajuste/{fator_id}/excluir", response_class=HTMLResponse)
async def handle_delete_fator(request: Request, fator_id: int):
    async with httpx.AsyncClient() as client:
        await client.delete(f"{API_BASE_URL}/fatores-ajuste/{fator_id}")
    return RedirectResponse(url="/fatores-ajuste", status_code=303)

# app/routers/pages.py (adicionar ao final do arquivo)

# --- ROTAS PARA PROJETOS ---

@router.get("/projetos", response_class=HTMLResponse)
async def list_projetos_page(
    request: Request,
    nome_filter: Optional[str] = None, # <-- NOVO
    cliente_id_filter: Optional[str] = None, # <-- NOVO (como string)
):
    """
    Renderiza a página que lista os projetos, aplicando filtros.
    """
    params = {}
    if nome_filter:
        params["nome_filter"] = nome_filter
    if cliente_id_filter:
        params["cliente_id_filter"] = cliente_id_filter

    async with httpx.AsyncClient() as client:
        # Busca os projetos já com os filtros
        response_projetos = await client.get(f"{API_BASE_URL}/projetos/", params=params)
        
        # Busca TODOS os clientes para popular o combobox de filtro
        response_clientes = await client.get(f"{API_BASE_URL}/clientes/")

    projetos = response_projetos.json() if response_projetos.status_code == 200 else []
    clientes = response_clientes.json() if response_clientes.status_code == 200 else []

    return templates.TemplateResponse("projetos/list.html", {
        "request": request,
        "projetos": projetos,
        "clientes": clientes, # Passa a lista de clientes para o template
        "nome_filter": nome_filter, # Devolve os filtros para a tela
        "cliente_id_filter": cliente_id_filter, # Devolve os filtros para a tela
    })

@router.get("/projetos/novo", response_class=HTMLResponse)
async def create_projeto_form(request: Request):
    # Busca a lista de clientes para popular o combobox
    async with httpx.AsyncClient() as client:
        response = await client.get(f"{API_BASE_URL}/clientes/")
    clientes = response.json() if response.status_code == 200 else []
    return templates.TemplateResponse("projetos/form.html", {"request": request, "clientes": clientes})

@router.post("/projetos/novo", response_class=HTMLResponse)
async def handle_create_projeto(request: Request, nome: str = Form(...), cliente_id: int = Form(...)):
    payload = {"nome": nome, "cliente_id": cliente_id}
    async with httpx.AsyncClient() as client:
        response = await client.post(f"{API_BASE_URL}/projetos/", json=payload)
    if response.status_code == 201:
        return RedirectResponse(url="/projetos", status_code=303)
    # Lógica de erro
    return RedirectResponse(url="/projetos/novo", status_code=303) # Simplificado

@router.get("/projetos/{projeto_id}/editar", response_class=HTMLResponse)
async def edit_projeto_form(request: Request, projeto_id: int):
    async with httpx.AsyncClient() as client:
        # Busca o projeto específico
        proj_resp = await client.get(f"{API_BASE_URL}/projetos/{projeto_id}")
        # Busca TODOS os clientes para o combobox
        cli_resp = await client.get(f"{API_BASE_URL}/clientes/")
    
    if proj_resp.status_code == 200:
        projeto = proj_resp.json()
        clientes = cli_resp.json() if cli_resp.status_code == 200 else []
        return templates.TemplateResponse("projetos/edit.html", {
            "request": request,
            "projeto": projeto,
            "clientes": clientes
        })
    return RedirectResponse(url="/projetos", status_code=303)

@router.post("/projetos/{projeto_id}/editar", response_class=HTMLResponse)
async def handle_edit_projeto(request: Request, projeto_id: int, nome: str = Form(...), cliente_id: int = Form(...)):
    payload = {"nome": nome, "cliente_id": cliente_id}
    async with httpx.AsyncClient() as client:
        response = await client.patch(f"{API_BASE_URL}/projetos/{projeto_id}", json=payload)
    return RedirectResponse(url="/projetos", status_code=303)

@router.get("/projetos/{projeto_id}/excluir", response_class=HTMLResponse)
async def delete_projeto_form(request: Request, projeto_id: int):
    async with httpx.AsyncClient() as client:
        response = await client.get(f"{API_BASE_URL}/projetos/{projeto_id}")
    if response.status_code == 200:
        projeto = response.json()
        return templates.TemplateResponse("projetos/delete.html", {"request": request, "projeto": projeto})
    return RedirectResponse(url="/projetos", status_code=303)

@router.post("/projetos/{projeto_id}/excluir", response_class=HTMLResponse)
async def handle_delete_projeto(request: Request, projeto_id: int):
    async with httpx.AsyncClient() as client:
        await client.delete(f"{API_BASE_URL}/projetos/{projeto_id}")
    return RedirectResponse(url="/projetos", status_code=303)