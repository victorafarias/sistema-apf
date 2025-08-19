# app/main.py

from fastapi import FastAPI

# Cria uma instância da aplicação FastAPI
# O título e a versão são úteis para a documentação automática
app = FastAPI(
    title="Sistema de Gerenciamento de Contagens de Pontos de Função",
    version="0.1.0"
)

# Define uma rota (endpoint) para a raiz da API ("/")
# O decorador @app.get("/") informa ao FastAPI que esta função
# deve responder a requisições HTTP GET na URL raiz.
@app.get("/", tags=["Root"])
def read_root():
    """
    Endpoint raiz que retorna uma mensagem de boas-vindas.
    Útil para verificar se a API está no ar.
    """
    return {"message": "Bem-vindo ao Sistema de Gerenciamento de APF!"}

# Aqui adicionaremos mais código conforme desenvolvemos as funcionalidades.