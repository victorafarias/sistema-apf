# app/routers/funcoes.py

from fastapi import APIRouter, Depends, UploadFile, File, HTTPException
from fastapi.responses import JSONResponse
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession
import pandas as pd
import io
from pydantic import BaseModel
from typing import List

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

        df_header_8.ffill(axis=1, inplace=True)

        header_list = []
        for col_idx in range(len(df_header_9.columns)): # Itera pela linha 9 que tem o número correto de colunas de dados
            val_8 = str(df_header_8.iat[0, col_idx]).strip() if col_idx < len(df_header_8.columns) and pd.notna(df_header_8.iat[0, col_idx]) else ""
            val_9 = str(df_header_9.iat[0, col_idx]).strip() if pd.notna(df_header_9.iat[0, col_idx]) else ""
            
            header = val_9 if val_9 and 'unnamed' not in val_9.lower() else val_8
            if val_8 and val_9 and val_8 != val_9 and 'unnamed' not in val_9.lower():
                header = f"{val_8} - {val_9}"

            header_list.append(header)
        
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


# (O restante do arquivo funcoes.py continua o mesmo...)
@router.post("/contagem/{contagem_id}/validate_step2")
async def validate_step2(
    contagem_id: int,
    session: AsyncSession = Depends(get_session),
):
    if contagem_id not in db_temp or "dados_importados" not in db_temp[contagem_id]:
        raise HTTPException(status_code=404, detail="Dados da importação não encontrados. Por favor, inicie o processo novamente.")

    dados_planilha = db_temp[contagem_id]["dados_importados"]
    
    tipos_projeto_planilha = {
        str(linha['Tipo Projeto']).strip() 
        for linha in dados_planilha if linha.get('Tipo Projeto') and pd.notna(linha['Tipo Projeto'])
    }
    
    result = await session.exec(select(FatorAjuste))
    fatores_existentes_db = result.all()
    nomes_fatores_db = {fator.nome for fator in fatores_existentes_db}

    nomes_fatores_novos = tipos_projeto_planilha - nomes_fatores_db

    fatores_novos_para_frontend = []
    for nome_novo in nomes_fatores_novos:
        # Renomeamos a coluna 'Fator Ajuste' para 'Fator Ajuste - Fator' na logica aprimorada
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