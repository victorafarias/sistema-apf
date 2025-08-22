# app/routers/funcoes.py

from fastapi import APIRouter, Depends, UploadFile, File, HTTPException
from fastapi.params import Body
from fastapi import Body
from fastapi.responses import JSONResponse
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession
import pandas as pd
import io
from pydantic import BaseModel
from typing import List
from app.services import calculation

from app.database import get_session
from app.models import Contagem, FatorAjuste

router = APIRouter(
    prefix="/funcoes",
    tags=["funcoes"],
)

db_temp = {}

@router.post("/contagem/{contagem_id}/upload_step1")
async def upload_step1(
    contagem_id: int,
    session: AsyncSession = Depends(get_session),
    file: UploadFile = File(...)
):
    print("[DEBUG] Iniciando upload_step1 para contagem_id:", contagem_id)
    contagem = await session.get(Contagem, contagem_id)
    if not contagem:
        raise HTTPException(status_code=404, detail="Contagem não encontrada")

    metodo_map = {"Detalhada": "AFP - Detalhada", "Estimada": "AFP - Estimativa"}
    sheet_name = metodo_map.get(contagem.metodo_contagem.value)
    if not sheet_name:
        raise HTTPException(status_code=400, content={"message": "Método de contagem inválido."})

    try:
        contents = await file.read()
        buffer = io.BytesIO(contents)
        
        xls = pd.ExcelFile(buffer)
        if sheet_name not in xls.sheet_names:
            raise HTTPException(status_code=400, detail=f"A guia '{sheet_name}' não foi encontrada.")

        print(f"[DEBUG] Lendo a guia: {sheet_name}")

        df_header_8 = pd.read_excel(xls, sheet_name=sheet_name, header=None, skiprows=7, nrows=1)
        df_header_9 = pd.read_excel(xls, sheet_name=sheet_name, header=None, skiprows=8, nrows=1)

        # --- LÓGICA DE PREENCHIMENTO E LEITURA DO CABEÇALHO CORRIGIDA ---
        # Removido: df_header_8.ffill(axis=1, inplace=True) -> Causava o NotImplementedError

        header_list = []
        last_header_8 = "" # Variável para guardar o último valor válido da linha 8
        for col_idx in range(len(df_header_9.columns)):
            
            # Pega o valor da linha 8 e atualiza nossa variável de controle se não for nulo
            if col_idx < len(df_header_8.columns) and pd.notna(df_header_8.iat[0, col_idx]):
                last_header_8 = str(df_header_8.iat[0, col_idx]).strip()

            val_8 = last_header_8 # Usa o último valor válido visto
            val_9 = str(df_header_9.iat[0, col_idx]).strip() if pd.notna(df_header_9.iat[0, col_idx]) else ""
            
            header = val_9 if val_9 and 'unnamed' not in val_9.lower() else val_8
            if val_8 and val_9 and val_8 != val_9 and 'unnamed' not in val_9.lower():
                header = f"{val_8} - {val_9}"

            header_list.append(header)
        # --- FIM DA CORREÇÃO ---
        
        print("[DEBUG] Cabeçalhos gerados antes da unicidade:", header_list)

        final_headers = []
        counts = {}
        for h in header_list:
            if h in counts:
                counts[h] += 1
                final_headers.append(f"{h}_{counts[h]}")
            else:
                counts[h] = 0
                final_headers.append(h)

        print("[DEBUG] Cabeçalhos finais e únicos:", final_headers)

        df_data = pd.read_excel(xls, sheet_name=sheet_name, skiprows=9, header=None)
        
        num_cols = min(len(final_headers), len(df_data.columns))
        df_data = df_data.iloc[:, :num_cols]
        df_data.columns = final_headers[:num_cols]
        
        df_data.dropna(axis=1, how='all', inplace=True)
        df_data.dropna(axis=0, how='all', inplace=True)
        
        df_data = df_data.astype(object).where(pd.notnull(df_data), None)
        
        print("[DEBUG] Colunas do DataFrame antes de converter para dict:", list(df_data.columns))
        data_records = df_data.to_dict(orient='records')
        print("[DEBUG] Conversão para dicionário bem-sucedida.")

        db_temp[contagem_id] = {
            "original_filename": file.filename,
            "dados_importados": data_records
        }
        
        return JSONResponse(status_code=200, content={
            "message": "Arquivo lido com sucesso!", "filename": file.filename,
            "total_records": len(data_records), "headers": list(df_data.columns),
            "data_preview": data_records[:5]
        })
    except Exception as e:
        print(f"ERRO DETALHADO NO PROCESSAMENTO DO ARQUIVO: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Ocorreu um erro no servidor ao processar o arquivo: {e}")


@router.post("/contagem/{contagem_id}/validate_step2")
async def validate_step2(
    contagem_id: int,
    session: AsyncSession = Depends(get_session),
):
    if contagem_id not in db_temp or "dados_importados" not in db_temp[contagem_id]:
        raise HTTPException(status_code=404, detail="Dados da importação não encontrados. Por favor, inicie o processo novamente.")

    dados_planilha = db_temp[contagem_id]["dados_importados"]
    
    # --- INÍCIO DA ALTERAÇÃO ---
    texto_a_ignorar = "Só inserir linhas antes desta."

    # Pega todos os nomes únicos de 'Tipo Projeto', aplicando o novo filtro
    tipos_projeto_planilha = {
        str(linha['Tipo Projeto']).strip() 
        for linha in dados_planilha if (
            linha.get('Tipo Projeto') and
            pd.notna(linha['Tipo Projeto']) and
            str(linha['Tipo Projeto']).strip() != texto_a_ignorar
        )
    }
    # --- FIM DA ALTERAÇÃO ---
    
    result = await session.exec(select(FatorAjuste))
    fatores_existentes_db = result.all()
    nomes_fatores_db = {fator.nome for fator in fatores_existentes_db}

    nomes_fatores_novos = tipos_projeto_planilha - nomes_fatores_db

    fatores_novos_para_frontend = []
    for nome_novo in nomes_fatores_novos:
        nome_coluna_fator = 'Fator Ajuste' if 'Fator Ajuste' in dados_planilha[0] else 'Fator Ajuste - Fator'
        
        linha_correspondente = next(
            (item for item in dados_planilha if str(item.get('Tipo Projeto', '')).strip() == nome_novo),
            None
        )
        if linha_correspondente:
            fatores_novos_para_frontend.append({
                "nome": nome_novo,
                "fator": linha_correspondente.get(nome_coluna_fator, 0.0)
            })
            
    return JSONResponse(
        status_code=200,
        content={"fatores_novos": fatores_novos_para_frontend}
    )


class FatorAjusteNovo(BaseModel):
    nome: str
    fator: float
    tipo_ajuste: str

@router.post("/contagem/{contagem_id}/create_fatores_step2")
async def create_fatores_step2(
    contagem_id: int,
    novos_fatores: List[FatorAjusteNovo],
    session: AsyncSession = Depends(get_session)
):
    if not novos_fatores:
        return JSONResponse(status_code=200, content={"message": "Nenhum novo fator para adicionar. Prosseguindo."})

    try:
        for fator_data in novos_fatores:
            db_fator = FatorAjuste.model_validate(fator_data)
            session.add(db_fator)
        
        await session.commit()
        
        return JSONResponse(status_code=201, content={"message": "Fatores de ajuste criados com sucesso!"})

    except Exception as e:
        await session.rollback()
        print(f"Erro ao criar fatores de ajuste: {e}")
        raise HTTPException(status_code=500, detail="Ocorreu um erro ao salvar os novos fatores de ajuste.")
    
@router.post("/contagem/{contagem_id}/process_mapping_step3")
async def process_mapping_step3(
    contagem_id: int,
    mapeamento: dict = Body(...), # Recebe o mapeamento como {"Coluna Planilha": "campo_db", ...}
    session: AsyncSession = Depends(get_session)
):
    """
    Etapa 3: Recebe o mapeamento, renomeia os dados, busca IDs, calcula os PFs
    e prepara os dados para a pré-visualização.
    """
    if contagem_id not in db_temp or "dados_importados" not in db_temp[contagem_id]:
        raise HTTPException(status_code=404, detail="Dados da importação não encontrados.")

    dados_originais = db_temp[contagem_id]["dados_importados"]
    
    # 1. Renomeia as chaves dos dicionários com base no mapeamento recebido
    dados_mapeados = []
    for linha in dados_originais:
        nova_linha = {}
        for coluna_planilha, campo_db in mapeamento.items():
            if coluna_planilha in linha:
                nova_linha[campo_db] = linha[coluna_planilha]
        dados_mapeados.append(nova_linha)

    # 2. Busca todos os fatores de ajuste (incluindo os novos) para criar um mapa de nome -> id
    result = await session.exec(select(FatorAjuste))
    mapa_fatores = {fator.nome: fator for fator in result.all()}

    # 3. Enriquece os dados e executa os cálculos
    dados_processados = []
    for linha in dados_mapeados:
        # Pula linhas que não têm um 'Tipo Projeto' (agora mapeado para 'nome_fator_ajuste')
        nome_fator = linha.get("nome_fator_ajuste")
        if not nome_fator or pd.isna(nome_fator):
            continue

        fator_obj = mapa_fatores.get(str(nome_fator).strip())
        
        if fator_obj:
            linha['fator_ajuste_id'] = fator_obj.id
            # Adiciona o valor do fator para o cálculo
            linha['fator_ajuste'] = fator_obj.fator
        else:
            # Se por algum motivo não encontrar (não deveria acontecer), define valores padrão
            linha['fator_ajuste_id'] = None
            linha['fator_ajuste'] = 1.0

        # Garante que os campos numéricos são tratados corretamente
        linha['qtd_der'] = int(linha.get('qtd_der', 0) or 0)
        linha['qtd_rlr'] = int(linha.get('qtd_rlr', 0) or 0)

        # Executa o cálculo
        linha_calculada = calculation.calcular_pontos_de_funcao(linha)
        dados_processados.append(linha_calculada)

    # Salva os dados processados e prontos para a etapa final
    db_temp[contagem_id]["dados_processados"] = dados_processados
    
    return JSONResponse(status_code=200, content={
        "message": "Mapeamento processado e cálculos realizados com sucesso.",
        "total_records": len(dados_processados),
        "preview": dados_processados[:10] # Envia uma prévia para a Etapa 4
    })