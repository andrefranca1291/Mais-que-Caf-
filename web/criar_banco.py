from pathlib import Path

from conexao import conectar


def criar_banco():
    caminho_sql = Path(__file__).with_name("schema_postgres.sql")
    comandos_sql = caminho_sql.read_text(encoding="utf-8")

    conexao = conectar()
    try:
        cursor = conexao.cursor()
        try:
            for comando in comandos_sql.split(";"):
                if comando.strip():
                    cursor.execute(comando)
        finally:
            cursor.close()
        conexao.commit()
        print("Tabelas e relacionamentos criados com sucesso.")
    finally:
        conexao.close()


if __name__ == "__main__":
    criar_banco()
