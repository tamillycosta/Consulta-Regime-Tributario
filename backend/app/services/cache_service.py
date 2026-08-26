import sqlite3
import json
import os
from datetime import datetime
from typing import Optional, Dict, Any

DB_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "data")
DB_PATH = os.path.join(DB_DIR, "cnpj_cache.db")

def init_db():
    os.makedirs(DB_DIR, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS cnpj_cache (
            cnpj TEXT PRIMARY KEY,
            consulted_at TEXT,
            razao_social TEXT,
            nome_fantasia TEXT,
            situacao_cadastral TEXT,
            opcao_pelo_simples INTEGER,
            data_opcao_simples TEXT,
            data_exclusao_simples TEXT,
            opcao_pelo_mei INTEGER,
            data_opcao_mei TEXT,
            data_exclusao_mei TEXT,
            cnae_descricao TEXT,
            uf TEXT,
            municipio TEXT,
            raw_json TEXT
        )
    """)
    conn.commit()
    conn.close()

def get_cached_cnpj(cnpj: str, max_age_days: int = 30) -> Optional[Dict[str, Any]]:
    clean_cnpj = "".join(filter(str.isdigit, str(cnpj))).zfill(14)
    if not os.path.exists(DB_PATH):
        init_db()
        return None

    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM cnpj_cache WHERE cnpj = ?", (clean_cnpj,))
    row = cursor.fetchone()
    conn.close()

    if row:
        row_dict = dict(row)
        try:
            consulted_date = datetime.strptime(row_dict["consulted_at"], "%Y-%m-%d")
            days_old = (datetime.now() - consulted_date).days
            if days_old <= max_age_days:
                return {
                    "cnpj": row_dict["cnpj"],
                    "razao_social": row_dict["razao_social"],
                    "nome_fantasia": row_dict["nome_fantasia"],
                    "situacao_cadastral": row_dict["situacao_cadastral"],
                    "opcao_pelo_simples": bool(row_dict["opcao_pelo_simples"]) if row_dict["opcao_pelo_simples"] is not None else None,
                    "data_opcao_simples": row_dict["data_opcao_simples"],
                    "data_exclusao_simples": row_dict["data_exclusao_simples"],
                    "opcao_pelo_mei": bool(row_dict["opcao_pelo_mei"]) if row_dict["opcao_pelo_mei"] is not None else None,
                    "data_opcao_mei": row_dict["data_opcao_mei"],
                    "data_exclusao_mei": row_dict["data_exclusao_mei"],
                    "cnae_descricao": row_dict["cnae_descricao"],
                    "uf": row_dict["uf"],
                    "municipio": row_dict["municipio"],
                    "fonte": "CACHE",
                    "consulted_at": row_dict["consulted_at"]
                }
        except Exception:
            pass
    return None

def save_cached_cnpj(cnpj: str, data: Dict[str, Any]):
    clean_cnpj = "".join(filter(str.isdigit, str(cnpj))).zfill(14)
    if not os.path.exists(DB_PATH):
        init_db()

    today = datetime.now().strftime("%Y-%m-%d")
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    simples_val = 1 if data.get("opcao_pelo_simples") is True else (0 if data.get("opcao_pelo_simples") is False else None)
    mei_val = 1 if data.get("opcao_pelo_mei") is True else (0 if data.get("opcao_pelo_mei") is False else None)

    cursor.execute("""
        INSERT INTO cnpj_cache (
            cnpj, consulted_at, razao_social, nome_fantasia, situacao_cadastral,
            opcao_pelo_simples, data_opcao_simples, data_exclusao_simples,
            opcao_pelo_mei, data_opcao_mei, data_exclusao_mei,
            cnae_descricao, uf, municipio, raw_json
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(cnpj) DO UPDATE SET
            consulted_at=excluded.consulted_at,
            razao_social=excluded.razao_social,
            nome_fantasia=excluded.nome_fantasia,
            situacao_cadastral=excluded.situacao_cadastral,
            opcao_pelo_simples=excluded.opcao_pelo_simples,
            data_opcao_simples=excluded.data_opcao_simples,
            data_exclusao_simples=excluded.data_exclusao_simples,
            opcao_pelo_mei=excluded.opcao_pelo_mei,
            data_opcao_mei=excluded.data_opcao_mei,
            data_exclusao_mei=excluded.data_exclusao_mei,
            cnae_descricao=excluded.cnae_descricao,
            uf=excluded.uf,
            municipio=excluded.municipio,
            raw_json=excluded.raw_json
    """, (
        clean_cnpj,
        today,
        data.get("razao_social"),
        data.get("nome_fantasia"),
        data.get("situacao_cadastral"),
        simples_val,
        data.get("data_opcao_simples"),
        data.get("data_exclusao_simples"),
        mei_val,
        data.get("data_opcao_mei"),
        data.get("data_exclusao_mei"),
        data.get("cnae_descricao"),
        data.get("uf"),
        data.get("municipio"),
        json.dumps(data, ensure_ascii=False)
    ))
    conn.commit()
    conn.close()
