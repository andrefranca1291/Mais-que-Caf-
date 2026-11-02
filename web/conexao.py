import os
from urllib.parse import unquote, urlparse

import pg8000.dbapi


def conectar():
    """Abre conexão PostgreSQL a partir da DATABASE_URL do Render."""
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        raise RuntimeError(
            "A variável DATABASE_URL não foi configurada. "
            "Defina a URL do banco PostgreSQL nas variáveis de ambiente."
        )

    partes = urlparse(database_url)
    if not partes.hostname or not partes.username or not partes.path:
        raise RuntimeError("A DATABASE_URL do PostgreSQL está incompleta.")

    return pg8000.dbapi.connect(
        user=unquote(partes.username),
        password=unquote(partes.password or ""),
        host=partes.hostname,
        port=partes.port or 5432,
        database=unquote(partes.path.lstrip("/")),
        ssl_context=True,
        timeout=10,
    )
