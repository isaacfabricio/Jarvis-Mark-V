"""Módulos executor de intents — stubs para funcionalidades principais.

Adicionar funções concretas para:
- integração com Shein (conector para API / automação web)
- geração de planilhas com Power Query M
- exportação/integração com Power BI
- automações (agendamento, notificações)

Cada função deve receber os parâmetros extraídos pela NLU e retornar
um resultado ou lançar exceção em caso de erro.
"""
from __future__ import annotations
from typing import Dict, Any
import os


def execute_intent(intent: str, params: Dict[str, Any]) -> Dict[str, Any]:
    """Despacha a intent para o handler apropriado (ainda stubs)."""
    if intent == "fetch_orders":
        return fetch_orders(params)
    if intent == "manage_products":
        return manage_products(params)
    if intent == "generate_sheet":
        return generate_sheet(params)
    if intent == "build_dashboard":
        return build_dashboard(params)
    if intent == "web_search":
        return web_search(params)
    return {"status": "error", "message": f"Intent desconhecida: {intent}"}


# Stubs — implementar conforme as necessidades

def fetch_orders(params: Dict[str, Any]) -> Dict[str, Any]:
    """Buscar pedidos — placeholder que gera um CSV de exemplo.

    Parâmetros esperados (exemplos): from, to, status
    O handler cria um arquivo CSV em ./data/ e retorna o caminho para o usuário.
    """
    import csv
    import os
    from datetime import datetime

    os.makedirs("./data", exist_ok=True)
    ts = datetime.utcnow().strftime("%Y%m%dT%H%M%SZ")
    filename = f"./data/orders_{ts}.csv"

    # Exemplo de conteúdo — em produção isso viria da API Shein
    rows = [
        {"order_id": "1001", "date": "2026-08-10", "status": "shipped", "total": "49.90"},
        {"order_id": "1002", "date": "2026-08-12", "status": "processing", "total": "89.00"},
        {"order_id": "1003", "date": "2026-08-15", "status": "delivered", "total": "15.25"},
    ]

    fieldnames = ["order_id", "date", "status", "total"]
    with open(filename, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for r in rows:
            writer.writerow(r)

    return {"status": "ok", "action": "fetch_orders", "path": filename, "rows": len(rows), "params": params}



def manage_products(params: Dict[str, Any]) -> Dict[str, Any]:
    return {"status": "ok", "action": "manage_products", "params": params}


def generate_sheet(params: Dict[str, Any]) -> Dict[str, Any]:
    """Gerar planilha/Power Query M template a partir de um CSV.

    Params esperados (opcionais):
      - source: caminho para o CSV de entrada. Se não fornecido busca o último CSV em ./data/orders_*.csv
      - output: caminho para salvar o template (.m ou .pq)

    O template gerado é um exemplo M (Power Query) que carrega o CSV,
    promove cabeçalhos e tenta converter tipos básicos.
    """
    import glob
    import os as _os
    from datetime import datetime

    source = None
    if isinstance(params, dict):
        source = params.get("source")
    # Procurar último CSV em ./data se source não fornecido
    if not source:
        files = sorted(glob.glob("./data/orders_*.csv"), reverse=True)
        if files:
            source = files[0]
    if not source:
        return {"status": "error", "message": "Nenhum CSV fonte encontrado. Forneça params.source ou coloque ./data/orders_*.csv"}

    # Gera conteúdo M
    # Observação: path deve ser escapado para M; usaremos caminho relativo.
    m_template = f'''let
    Fonte = Csv.Document(File.Contents("{source}"), [Delimiter=",", Columns=null, Encoding=65001, QuoteStyle=QuoteStyle.Csv]),
    PromotedHeaders = Table.PromoteHeaders(Fonte, [PromoteAllScalars=true]),
    ChangedTypes = Table.TransformColumnTypes(PromotedHeaders, List.Transform(Table.ColumnNames(PromotedHeaders), each {"{"}#, type nullable text{"}"}))
in
    ChangedTypes'''

    _os.makedirs("./data", exist_ok=True)
    ts = datetime.utcnow().strftime("%Y%m%dT%H%M%SZ")
    output = params.get("output") if isinstance(params, dict) else None
    if not output:
        output = f"./data/powerquery_template_{ts}.m"

    with open(output, "w", encoding="utf-8") as f:
        f.write(m_template)

    return {"status": "ok", "action": "generate_sheet", "path": output, "source": source}



def build_dashboard(params: Dict[str, Any]) -> Dict[str, Any]:
    return {"status": "ok", "action": "build_dashboard", "params": params}


def web_search(params: Dict[str, Any]) -> Dict[str, Any]:
    """Handler que realiza buscas web usando Tavily.

    Espera parâmetro 'query' em params ou combinar todos os params em string.
    """
    # import local para evitar erro se tavily não estiver instalado
    try:
        from .tools.web_search import buscar_na_web
    except Exception as e:
        return {"status": "error", "message": f"Falha ao importar buscar_na_web: {e}"}

    query = params.get("query") if isinstance(params, dict) else None
    if not query:
        # montar query a partir de outros parâmetros
        if isinstance(params, dict) and params:
            # join key:val pairs
            qparts = [f"{k}={v}" for k, v in params.items()]
            query = " ".join(qparts)
        else:
            return {"status": "error", "message": "Nenhuma query fornecida para web_search"}

    # detecta simulate pela params ou pela variável de ambiente JARVIS_SIMULATE
    simulate = params.get("simulate") if isinstance(params, dict) and "simulate" in params else (os.getenv("JARVIS_SIMULATE") == "1")
    resp = buscar_na_web(query, simulate=simulate)

    # Se erro, propaga
    if resp.get("status") != "ok":
        return resp

    # Formatar e salvar resultado em ./data/search_<ts>.json
    import json
    from datetime import datetime
    import os as _os

    _os.makedirs("./data", exist_ok=True)
    ts = datetime.utcnow().strftime("%Y%m%dT%H%M%SZ")
    filename = f"./data/search_{ts}.json"
    out = {"query": query, "timestamp": ts, "results": resp.get("results")}
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=2)

    # Preparar uma versão resumida para retorno imediato
    summary = []
    for r in resp.get("results", []):
        url = r.get("url")
        content = r.get("content", "")
        snippet = content[:200].replace("\n", " ")
        summary.append({"url": url, "snippet": snippet})

    return {"status": "ok", "action": "web_search", "path": filename, "summary": summary}


