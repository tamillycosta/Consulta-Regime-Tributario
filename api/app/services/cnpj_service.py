import asyncio
import httpx
from typing import Dict, Any, List, Optional
from datetime import datetime
from app.services.cache_service import get_cached_cnpj, save_cached_cnpj

# Semaphore to control concurrent API requests
SEMAPHORE = asyncio.Semaphore(4)

def format_cnpj(cnpj_raw: Any) -> str:
    digits = "".join(filter(str.isdigit, str(cnpj_raw)))
    return digits.zfill(14)

def determine_regime_resumo(
    opcao_simples: Optional[bool],
    data_exclusao_simples: Optional[str],
    opcao_mei: Optional[bool],
    situacao_cadastral: Optional[str]
) -> str:
    if situacao_cadastral and situacao_cadastral.upper() in ["BAIXADA", "INAPTOS", "INAPTA", "SUSPENSA", "NULA"]:
        return f"Situação Cadastral: {situacao_cadastral.upper()}"

    if opcao_mei is True:
        return "Optante pelo MEI"
    elif opcao_simples is True:
        return "Optante pelo Simples Nacional"
    elif data_exclusao_simples:
        return f"Excluído do Simples em {data_exclusao_simples}"
    elif opcao_simples is False:
        return "Não Optante pelo Simples (Lucro Presumido/Real)"
    else:
        return "Regime Não Informado / Outro"

async def fetch_brasilapi(client: httpx.AsyncClient, cnpj: str) -> Optional[Dict[str, Any]]:
    url = f"https://brasilapi.com.br/api/cnpj/v1/{cnpj}"
    try:
        resp = await client.get(url, timeout=10.0)
        if resp.status_code == 200:
            data = resp.json()
            opcao_simples = data.get("opcao_pelo_simples")
            opcao_mei = data.get("opcao_pelo_mei")
            situacao = data.get("descricao_situacao_cadastral", "ATIVA")
            data_excl_simples = data.get("data_exclusao_do_simples")
            
            resumo = determine_regime_resumo(opcao_simples, data_excl_simples, opcao_mei, situacao)

            return {
                "cnpj": cnpj,
                "razao_social": data.get("razao_social", ""),
                "nome_fantasia": data.get("nome_fantasia", ""),
                "situacao_cadastral": situacao,
                "opcao_pelo_simples": opcao_simples,
                "data_opcao_simples": data.get("data_opcao_pelo_simples"),
                "data_exclusao_simples": data_excl_simples,
                "opcao_pelo_mei": opcao_mei,
                "data_opcao_mei": data.get("data_opcao_pelo_mei"),
                "data_exclusao_mei": data.get("data_exclusao_do_mei"),
                "regime_resumo": resumo,
                "cnae_descricao": data.get("cnae_fiscal_descricao", ""),
                "uf": data.get("uf", ""),
                "municipio": data.get("municipio", ""),
                "fonte": "BrasilAPI",
                "consulted_at": datetime.now().strftime("%Y-%m-%d %H:%M"),
                "erro": None
            }
    except Exception:
        pass
    return None

async def fetch_minhareceita(client: httpx.AsyncClient, cnpj: str) -> Optional[Dict[str, Any]]:
    url = f"https://minhareceita.org/{cnpj}"
    try:
        resp = await client.get(url, timeout=10.0)
        if resp.status_code == 200:
            data = resp.json()
            opcao_simples = data.get("opcao_pelo_simples")
            opcao_mei = data.get("opcao_pelo_mei")
            situacao = data.get("descricao_situacao_cadastral", "ATIVA")
            data_excl_simples = data.get("data_exclusao_do_simples")

            resumo = determine_regime_resumo(opcao_simples, data_excl_simples, opcao_mei, situacao)

            return {
                "cnpj": cnpj,
                "razao_social": data.get("razao_social", ""),
                "nome_fantasia": data.get("nome_fantasia", ""),
                "situacao_cadastral": situacao,
                "opcao_pelo_simples": opcao_simples,
                "data_opcao_simples": data.get("data_opcao_pelo_simples"),
                "data_exclusao_simples": data_excl_simples,
                "opcao_pelo_mei": opcao_mei,
                "data_opcao_mei": data.get("data_opcao_mei"),
                "data_exclusao_mei": data.get("data_exclusao_do_mei"),
                "regime_resumo": resumo,
                "cnae_descricao": data.get("cnae_fiscal_descricao", ""),
                "uf": data.get("uf", ""),
                "municipio": data.get("municipio", ""),
                "fonte": "MinhaReceita",
                "consulted_at": datetime.now().strftime("%Y-%m-%d %H:%M"),
                "erro": None
            }
    except Exception:
        pass
    return None

async def query_single_cnpj(client: httpx.AsyncClient, cnpj_raw: str, nome_planilha: str = "") -> Dict[str, Any]:
    cnpj_formatted = format_cnpj(cnpj_raw)
    
    if len(cnpj_formatted) != 14 or cnpj_formatted == "00000000000000":
        return {
            "cnpj": cnpj_raw,
            "nome_planilha": nome_planilha,
            "razao_social": nome_planilha,
            "nome_fantasia": "",
            "situacao_cadastral": "INVÁLIDO",
            "opcao_pelo_simples": None,
            "data_opcao_simples": None,
            "data_exclusao_simples": None,
            "opcao_pelo_mei": None,
            "data_opcao_mei": None,
            "data_exclusao_mei": None,
            "regime_resumo": "CNPJ Inválido",
            "cnae_descricao": "",
            "uf": "",
            "municipio": "",
            "fonte": "SISTEMA",
            "consulted_at": datetime.now().strftime("%Y-%m-%d %H:%M"),
            "erro": "CNPJ deve possuir 14 dígitos numéricos"
        }

    # Check Cache
    cached = get_cached_cnpj(cnpj_formatted)
    if cached:
        cached["nome_planilha"] = nome_planilha
        if not cached.get("razao_social") and nome_planilha:
            cached["razao_social"] = nome_planilha
        cached["regime_resumo"] = determine_regime_resumo(
            cached.get("opcao_pelo_simples"),
            cached.get("data_exclusao_simples"),
            cached.get("opcao_pelo_mei"),
            cached.get("situacao_cadastral")
        )
        cached["erro"] = None
        return cached

    async with SEMAPHORE:
        # Politeness sleep between parallel API calls
        await asyncio.sleep(0.15)
        
        # Primary: BrasilAPI
        res = await fetch_brasilapi(client, cnpj_formatted)
        if not res:
            # Fallback: MinhaReceita
            await asyncio.sleep(0.2)
            res = await fetch_minhareceita(client, cnpj_formatted)

        if res:
            res["nome_planilha"] = nome_planilha
            save_cached_cnpj(cnpj_formatted, res)
            return res
        else:
            return {
                "cnpj": cnpj_formatted,
                "nome_planilha": nome_planilha,
                "razao_social": nome_planilha,
                "nome_fantasia": "",
                "situacao_cadastral": "DESCONHECIDA",
                "opcao_pelo_simples": None,
                "data_opcao_simples": None,
                "data_exclusao_simples": None,
                "opcao_pelo_mei": None,
                "data_opcao_mei": None,
                "data_exclusao_mei": None,
                "regime_resumo": "Não Encontrado / Falha na Consulta",
                "cnae_descricao": "",
                "uf": "",
                "municipio": "",
                "fonte": "FALHA",
                "consulted_at": datetime.now().strftime("%Y-%m-%d %H:%M"),
                "erro": "Serviços da Receita temporariamente indisponíveis para este CNPJ"
            }
