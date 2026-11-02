import os

import psycopg


def conectar():
    """Abre uma conexão PostgreSQL usando a variável DATABASE_URL."""
    database_url = os.getenv("DATABASE_URL")

    if not database_url:
        raise RuntimeError(
            "A variável DATABASE_URL não foi configurada. "
            "Defina a URL do banco PostgreSQL nas variáveis de ambiente."
        )

    return psycopg.connect(database_url, connect_timeout=10)
