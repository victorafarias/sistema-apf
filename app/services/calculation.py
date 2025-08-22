# app/services/calculation.py

from decimal import Decimal, ROUND_HALF_UP

def _calcular_complexidade_ali(qtd_rlr: int, qtd_der: int) -> str:
    if qtd_rlr == 1:
        if 1 <= qtd_der <= 50:
            return "Baixa"
        return "Média"
    if 2 <= qtd_rlr <= 5:
        if 1 <= qtd_der <= 19:
            return "Baixa"
        if 20 <= qtd_der <= 50:
            return "Média"
        return "Alta"
    if qtd_rlr >= 6:
        if 1 <= qtd_der <= 19:
            return "Média"
        return "Alta"
    return "N/A"

def _calcular_complexidade_aie(qtd_rlr: int, qtd_der: int) -> str:
    # AIE usa a mesma matriz de complexidade que ALI
    return _calcular_complexidade_ali(qtd_rlr, qtd_der)

def _calcular_complexidade_ee_ce(qtd_rlr: int, qtd_der: int) -> str:
    if 0 <= qtd_rlr <= 1:
        if 1 <= qtd_der <= 15:
            return "Baixa"
        return "Média"
    if qtd_rlr == 2:
        if 1 <= qtd_der <= 4:
            return "Baixa"
        if 5 <= qtd_der <= 15:
            return "Média"
        return "Alta"
    if qtd_rlr >= 3:
        if 1 <= qtd_der <= 4:
            return "Média"
        return "Alta"
    return "N/A"
    
def _calcular_complexidade_se(qtd_rlr: int, qtd_der: int) -> str:
    if 0 <= qtd_rlr <= 1:
        if 1 <= qtd_der <= 19:
            return "Baixa"
        return "Média"
    if 2 <= qtd_rlr <= 3:
        if 1 <= qtd_der <= 5:
            return "Baixa"
        if 6 <= qtd_der <= 19:
            return "Média"
        return "Alta"
    if qtd_rlr >= 4:
        if 1 <= qtd_der <= 5:
            return "Média"
        return "Alta"
    return "N/A"


def calcular_pontos_de_funcao(linha_funcao: dict) -> dict:
    """
    Calcula Complexidade, PF Bruto e PF Líquido para uma única função.
    Espera um dicionário com 'tipo_funcao', 'qtd_der', 'qtd_rlr', e 'fator_ajuste'.
    """
    tipo = linha_funcao.get("tipo_funcao")
    qtd_der = int(linha_funcao.get("qtd_der", 0))
    qtd_rlr = int(linha_funcao.get("qtd_rlr", 0))
    fator_ajuste = float(linha_funcao.get("fator_ajuste", 1.0))

    complexidade = "N/A"
    pf_bruto = 0

    # Pesos do PF Bruto por tipo e complexidade
    pesos = {
        "ALI": {"Baixa": 7, "Média": 10, "Alta": 15},
        "AIE": {"Baixa": 5, "Média": 7, "Alta": 10},
        "EE":  {"Baixa": 3, "Média": 4, "Alta": 6},
        "CE":  {"Baixa": 3, "Média": 4, "Alta": 6},
        "SE":  {"Baixa": 4, "Média": 5, "Alta": 7},
    }

    if tipo in ["ALI", "AIE"]:
        complexidade = _calcular_complexidade_ali(qtd_rlr, qtd_der)
    elif tipo == "EE":
        complexidade = _calcular_complexidade_ee_ce(qtd_rlr, qtd_der)
    elif tipo == "CE":
        complexidade = _calcular_complexidade_ee_ce(qtd_rlr, qtd_der) # Usa a mesma matriz de EE
    elif tipo == "SE":
        complexidade = _calcular_complexidade_se(qtd_rlr, qtd_der)
    
    if tipo in pesos and complexidade in pesos[tipo]:
        pf_bruto = pesos[tipo][complexidade]

    # Caso especial para INM
    if tipo == "INM":
        # Para INM, qtd_der pode representar o valor a ser multiplicado
        # Adapte se o nome da coluna for outro (ex: qtd_inm)
        pf_bruto = qtd_der * fator_ajuste
        pf_liquido = pf_bruto
        complexidade = "N/A"
    else:
        # Arredondamento bancário (duas casas decimais)
        pf_liquido = float(
            Decimal(pf_bruto * fator_ajuste).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
        )

    linha_funcao["complexidade"] = complexidade
    linha_funcao["ponto_de_funcao_bruto"] = pf_bruto
    linha_funcao["ponto_de_funcao_liquido"] = pf_liquido
    
    return linha_funcao