# app/routers/pages.py

import httpx
from fastapi import APIRouter, Request, Depends, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from loguru import logger

router = APIRouter(tags=["Pages"])
templates = Jinja2Templates(directory="templates")

# URL base da nossa própria API
API_BASE_URL = "http://127.0.0.1:8000/api"

@router.get("/clientes", response_class=HTMLResponse)
async def list_clientes_page(request: Request):
    """
    Renderiza a página que lista os clientes.
    """
    async with httpx.AsyncClient() as client:
        # Chama o nosso endpoint da API para obter a lista de clientes
        response = await client.get(f"{API_BASE_URL}/clientes")
    
    clientes = []
    if response.status_code == 200:
        clientes = response.json()
    else:
        # Aqui poderíamos adicionar uma mensagem de erro na página
        pass

    # Renderiza o template HTML, passando os dados dos clientes
    return templates.TemplateResponse("clientes_list.html", {
        "request": request,
        "clientes": clientes
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
        response = await client.post(f"{API_BASE_URL}/clientes", json={"nome": nome})
    
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