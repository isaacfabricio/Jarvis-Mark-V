"""Pipeline ETL local para arquivos CSV.

O núcleo do Jarvis usa esta função tanto pela API HTTP quanto pelo WebSocket.
Ela não depende de serviços externos e retorna apenas valores serializáveis em
JSON para que possa ser usada em jobs em segundo plano.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pandas as pd


def _read_csv(path: Path) -> pd.DataFrame:
    """Lê CSVs comuns exportados por Excel e ferramentas web."""

    last_error: Exception | None = None
    for encoding in ("utf-8-sig", "utf-8", "latin-1"):
        try:
            return pd.read_csv(path, encoding=encoding)
        except UnicodeDecodeError as error:
            last_error = error

    if last_error is not None:
        raise last_error
    return pd.read_csv(path)


def executar_pipeline_etl_csv(caminho: str | Path) -> dict[str, Any]:
    """Lê um CSV, normaliza sua estrutura básica e retorna um resumo.

    A função mantém o arquivo de origem intacto. O resultado contém uma
    amostra limitada para evitar que uma resposta de API carregue o dataset
    inteiro em memória.
    """

    source = Path(caminho).expanduser()
    if not source.is_file():
        raise FileNotFoundError(f"Arquivo CSV não encontrado: {source}")

    frame = _read_csv(source)
    frame.columns = [str(column).strip() for column in frame.columns]
    frame = frame.dropna(how="all")

    preview = frame.head(10).where(frame.head(10).notna(), None).to_dict(
        orient="records"
    )
    return {
        "status": "ok",
        "source": str(source),
        "rows": int(len(frame)),
        "columns": [str(column) for column in frame.columns],
        "preview": preview,
    }
