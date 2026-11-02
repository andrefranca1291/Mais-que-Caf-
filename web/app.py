import os
import re
from datetime import date, datetime, time, timedelta
from decimal import Decimal, InvalidOperation

from flask import Flask, render_template, request, redirect, url_for

from conexao import conectar

app = Flask(__name__)

def normalizar_telefone(telefone):
    """Retorna somente os dígitos e remove o código do Brasil quando informado."""
    digitos = re.sub(r"\D", "", telefone or "")
    if digitos.startswith("55") and len(digitos) in (12, 13):
        digitos = digitos[2:]
    return digitos


def formatar_moeda(valor):
    numero = f"{Decimal(str(valor or 0)):,.2f}"
    numero = numero.replace(",", "X").replace(".", ",").replace("X", ".")
    return f"R$ {numero}"

@app.route("/")
def inicio():
    return render_template("index.html")

@app.route("/clientes")
def listar_clientes():
    conexao = None

    try:
        conexao = conectar()
        cursor = conexao.cursor()
        cursor.execute("""
            SELECT id_cliente, nome, email, telefone
            FROM Cliente
            ORDER BY id_cliente ASC
        """)
        clientes = cursor.fetchall()

        return render_template(
            "clientes.html",
            clientes=clientes,
            aviso=request.args.get("aviso"),
            tipo_aviso=request.args.get("tipo", "sucesso")
        )

    except Exception as erro:
        return f"Erro ao consultar clientes: {erro}", 500

    finally:
        if conexao:
            conexao.close()

@app.route("/produtos")
def listar_produtos():
    conexao = None

    try:
        conexao = conectar()
        cursor = conexao.cursor()
        cursor.execute("""
            SELECT id_produto, nome, descricao, preco, categoria
            FROM Produto
            ORDER BY id_produto ASC
        """)
        produtos = cursor.fetchall()

        return render_template("produtos.html", produtos=produtos)

    except Exception as erro:
        return f"Erro ao consultar produtos: {erro}", 500

    finally:
        if conexao:
            conexao.close()

@app.route("/pedidos")
def listar_pedidos():
    conexao = None

    try:
        conexao = conectar()
        cursor = conexao.cursor()
        cursor.execute("""
            SELECT
                p.id_pedido,
                c.nome,
                p.data_pedido,
                p.valor_total,
                p.status,
                pg.tipo_pagamento,
                pg.status_pagamento,
                e.status_entrega
            FROM Pedido p
            INNER JOIN Cliente c
                ON p.id_cliente = c.id_cliente
            LEFT JOIN Pagamento pg
                ON p.id_pedido = pg.id_pedido
            LEFT JOIN Entrega e
                ON p.id_pedido = e.id_pedido
            ORDER BY p.id_pedido ASC
        """)
        pedidos = cursor.fetchall()

        return render_template("pedidos.html", pedidos=pedidos)

    except Exception as erro:
        return f"Erro ao consultar pedidos: {erro}", 500

    finally:
        if conexao:
            conexao.close()

@app.route("/relatorios")
def relatorios():
    primeiro_dia_mes = date.today().replace(day=1)
    inicio_texto = request.args.get(
        "data_inicio",
        primeiro_dia_mes.isoformat()
    )
    fim_texto = request.args.get(
        "data_fim",
        date.today().isoformat()
    )

    top_produtos = []
    vendas_diarias = []
    quantidade_pedidos = 0
    total_vendas = Decimal("0.00")
    ticket_medio = Decimal("0.00")
    erro = None
    conexao = None

    try:
        inicio = date.fromisoformat(inicio_texto)
        fim = date.fromisoformat(fim_texto)

        if inicio > fim:
            raise ValueError("A data inicial precisa ser anterior à final.")

        inicio_sql = datetime.combine(inicio, time.min)
        fim_sql = datetime.combine(fim + timedelta(days=1), time.min)

        conexao = conectar()
        cursor = conexao.cursor()

        cursor.execute("""
            SELECT
                pr.id_produto,
                pr.nome,
                SUM(ip.quantidade) AS unidades_vendidas,
                SUM(COALESCE(ip.subtotal, pr.preco * ip.quantidade))
                    AS receita
            FROM Item_Pedido ip
            INNER JOIN Pedido p
                ON p.id_pedido = ip.id_pedido
            INNER JOIN Produto pr
                ON pr.id_produto = ip.id_produto
            WHERE p.data_pedido >= %s
              AND p.data_pedido < %s
              AND (p.status IS NULL OR p.status <> 'Cancelado')
            GROUP BY pr.id_produto, pr.nome
            ORDER BY SUM(ip.quantidade) DESC, pr.nome
            LIMIT 10
        """, (inicio_sql, fim_sql))
        top_produtos = cursor.fetchall()

        cursor.execute("""
            SELECT
                COUNT(*),
                COALESCE(SUM(COALESCE(valor_total, 0)), 0)
            FROM Pedido
            WHERE data_pedido >= %s
              AND data_pedido < %s
              AND (status IS NULL OR status <> 'Cancelado')
        """, (inicio_sql, fim_sql))

        quantidade_pedidos, total_vendas = cursor.fetchone()
        total_vendas = Decimal(str(total_vendas))

        if quantidade_pedidos:
            ticket_medio = total_vendas / quantidade_pedidos

        cursor.execute("""
            SELECT
                CAST(data_pedido AS date) AS dia,
                COUNT(*) AS quantidade_pedidos,
                SUM(COALESCE(valor_total, 0)) AS vendas
            FROM Pedido
            WHERE data_pedido >= %s
              AND data_pedido < %s
              AND (status IS NULL OR status <> 'Cancelado')
            GROUP BY CAST(data_pedido AS date)
            ORDER BY dia
        """, (inicio_sql, fim_sql))
        vendas_diarias = cursor.fetchall()

    except Exception as ex:
        erro = str(ex)

    finally:
        if conexao:
            conexao.close()

    return render_template(
        "relatorios.html",
        data_inicio=inicio_texto,
        data_fim=fim_texto,
        top_produtos=top_produtos,
        vendas_diarias=vendas_diarias,
        quantidade_pedidos=quantidade_pedidos,
        total_vendas=formatar_moeda(total_vendas),
        ticket_medio=formatar_moeda(ticket_medio),
        formatar_moeda=formatar_moeda,
        erro=erro
    )

@app.route("/clientes/novo", methods=["GET", "POST"])
def novo_cliente():
    erro = None
    conexao = None

    if request.method == "POST":
        nome = request.form.get("nome", "").strip()
        email = request.form.get("email", "").strip()
        senha = request.form.get("senha", "")
        telefone = request.form.get("telefone", "").strip() or None
        telefone_normalizado = normalizar_telefone(telefone)

        if not nome or not email or not senha:
            erro = "Preencha nome, e-mail e senha."
        else:
            try:
                conexao = conectar()
                cursor = conexao.cursor()

                if telefone_normalizado:
                    cursor.execute(
                        """
                        SELECT telefone
                        FROM Cliente
                        WHERE telefone IS NOT NULL
                        """
                    )
                    telefones_existentes = cursor.fetchall()
                    telefone_duplicado = any(
                        normalizar_telefone(registro[0]) == telefone_normalizado
                        for registro in telefones_existentes
                    )

                    if telefone_duplicado:
                        erro = "Já existe um cliente cadastrado com esse telefone."

                if erro is None:
                    cursor.execute(
                        """
                        INSERT INTO Cliente (nome, email, senha, telefone)
                        VALUES (%s, %s, %s, %s)
                        """,
                        (nome, email, senha, telefone)
                    )
                    conexao.commit()
                    return redirect(url_for("listar_clientes"))

            except Exception as erro_banco:
                if conexao:
                    conexao.rollback()
                erro = f"Não foi possível salvar o cliente: {erro_banco}"

            finally:
                if conexao:
                    conexao.close()

    return render_template("cliente_form.html", erro=erro)


@app.route("/clientes/<int:id_cliente>/editar", methods=["GET", "POST"])
def editar_cliente(id_cliente):
    conexao = None
    erro = None
    cliente = None

    try:
        conexao = conectar()
        cursor = conexao.cursor()
        cursor.execute(
            """
            SELECT id_cliente, nome, email, telefone
            FROM Cliente
            WHERE id_cliente = %s
            """,
            (id_cliente,)
        )
        cliente = cursor.fetchone()

        if not cliente:
            return "Cliente não encontrado.", 404

        if request.method == "POST":
            nome = request.form.get("nome", "").strip()
            email = request.form.get("email", "").strip()
            telefone = request.form.get("telefone", "").strip() or None
            telefone_normalizado = normalizar_telefone(telefone)

            if not nome or not email:
                erro = "Preencha nome e e-mail."
            elif telefone_normalizado:
                cursor.execute(
                    """
                    SELECT id_cliente, telefone
                    FROM Cliente
                    WHERE telefone IS NOT NULL AND id_cliente <> %s
                    """,
                    (id_cliente,)
                )
                telefones_existentes = cursor.fetchall()
                if any(
                    normalizar_telefone(registro[1]) == telefone_normalizado
                    for registro in telefones_existentes
                ):
                    erro = "Já existe outro cliente cadastrado com esse telefone."

            if erro is None:
                cursor.execute(
                    """
                    UPDATE Cliente
                    SET nome = %s, email = %s, telefone = %s
                    WHERE id_cliente = %s
                    """,
                    (nome, email, telefone, id_cliente)
                )
                conexao.commit()
                return redirect(url_for("listar_clientes"))

            cliente = (id_cliente, nome, email, telefone)

    except Exception as erro_banco:
        if conexao:
            conexao.rollback()
        erro = f"Não foi possível atualizar o cliente: {erro_banco}"
    finally:
        if conexao:
            conexao.close()

    if cliente is None:
        return f"Erro ao abrir a edição do cliente: {erro}", 500

    return render_template("cliente_editar.html", cliente=cliente, erro=erro)


@app.route("/clientes/<int:id_cliente>/excluir", methods=["POST"])
def excluir_cliente(id_cliente):
    conexao = None

    try:
        conexao = conectar()
        cursor = conexao.cursor()
        cursor.execute("DELETE FROM Cliente WHERE id_cliente = %s", (id_cliente,))

        if cursor.rowcount == 0:
            return redirect(url_for(
                "listar_clientes",
                aviso="O cliente não foi encontrado.",
                tipo="erro"
            ))

        conexao.commit()
        return redirect(url_for(
            "listar_clientes",
            aviso="Cliente excluído com sucesso.",
            tipo="sucesso"
        ))

    except Exception as erro_banco:
        if conexao:
            conexao.rollback()
        codigo_erro = (
            getattr(erro_banco, "sqlstate", None)
            or getattr(erro_banco, "pgcode", None)
        )
        if codigo_erro == "23503":
            mensagem = "Este cliente possui pedido(s) vinculado(s) e não pode ser excluído."
        else:
            mensagem = "Não foi possível excluir o cliente. Cliente possui histórico de pedidos."
        return redirect(url_for(
            "listar_clientes",
            aviso=mensagem,
            tipo="erro"
        ))
    finally:
        if conexao:
            conexao.close()

@app.route("/produtos/novo", methods=["GET", "POST"])
def novo_produto():
    erro = None
    conexao = None

    if request.method == "POST":
        nome = request.form.get("nome", "").strip()
        descricao = request.form.get("descricao", "").strip() or None
        categoria = request.form.get("categoria", "").strip() or None
        preco_texto = request.form.get("preco", "").strip().replace(",", ".")

        if not nome or not preco_texto:
            erro = "Preencha o nome e o preço."
        else:
            try:
                preco = Decimal(preco_texto)

                if not preco.is_finite() or preco <= 0:
                    erro = "Informe um preço válido maior que zero."

            except InvalidOperation:
                erro = "Informe um preço válido."

        if erro is None:
            try:
                conexao = conectar()
                cursor = conexao.cursor()
                cursor.execute(
                    """
                    INSERT INTO Produto (nome, descricao, preco, categoria)
                    VALUES (%s, %s, %s, %s)
                    """,
                    (nome, descricao, preco, categoria)
                )
                conexao.commit()

                return redirect(url_for("listar_produtos"))

            except Exception as erro_banco:
                if conexao:
                    conexao.rollback()
                erro = f"Não foi possível salvar o produto: {erro_banco}"

            finally:
                if conexao:
                    conexao.close()

    return render_template("produto_form.html", erro=erro)

@app.route("/pedidos/novo", methods=["GET", "POST"])
def novo_pedido():
    erro = None
    conexao = None
    clientes = []
    produtos = []

    try:
        conexao = conectar()
        cursor = conexao.cursor()

        cursor.execute("""
            SELECT id_cliente, nome
            FROM Cliente
            ORDER BY id_cliente ASC
        """)
        clientes = cursor.fetchall()

        cursor.execute("""
            SELECT id_produto, nome, preco
            FROM Produto
            ORDER BY id_produto ASC
        """)
        produtos = cursor.fetchall()

        if request.method == "POST":
            try:
                id_cliente = int(request.form.get("id_cliente", ""))
            except ValueError:
                id_cliente = None

            tipo_pagamento = request.form.get("tipo_pagamento", "").strip()
            endereco = request.form.get("endereco", "").strip() or None

            itens_selecionados = []

            for numero in range(1, 6):
                produto_texto = request.form.get(
                    f"id_produto_{numero}", ""
                ).strip()
                quantidade_texto = request.form.get(
                    f"quantidade_{numero}", ""
                ).strip()

                if not produto_texto and not quantidade_texto:
                    continue

                if not produto_texto or not quantidade_texto:
                    erro = "Escolha um produto e informe sua quantidade."
                    break

                try:
                    id_produto = int(produto_texto)
                    quantidade = int(quantidade_texto)

                    if quantidade <= 0:
                        raise ValueError

                    itens_selecionados.append((id_produto, quantidade))

                except ValueError:
                    erro = "Confira os produtos e informe quantidades inteiras maiores que zero."
                    break

            if erro is None and not id_cliente:
                erro = "Selecione um cliente."

            if erro is None and not any(
                cliente[0] == id_cliente for cliente in clientes
            ):
                erro = "O cliente selecionado não foi encontrado."

            if erro is None and not itens_selecionados:
                erro = "Inclua pelo menos um produto no pedido."

            if erro is None and not tipo_pagamento:
                erro = "Selecione a forma de pagamento."

            if erro is None:
                precos_itens = []
                valor_total = Decimal("0.00")

                for id_produto, quantidade in itens_selecionados:
                    cursor.execute(
                        """
                        SELECT preco
                        FROM Produto
                        WHERE id_produto = %s
                        """,
                        (id_produto,)
                    )
                    resultado_preco = cursor.fetchone()

                    if not resultado_preco:
                        erro = "Um dos produtos selecionados não foi encontrado."
                        break

                    preco_unitario = Decimal(str(resultado_preco[0]))
                    subtotal = preco_unitario * quantidade
                    valor_total += subtotal

                    precos_itens.append(
                        (id_produto, quantidade, subtotal)
                    )

                if erro is None:
                    cursor.execute(
                        """
                        INSERT INTO Pedido (id_cliente, valor_total, status)
                        VALUES (%s, %s, %s)
                        RETURNING id_pedido
                        """,
                        (id_cliente, valor_total, "Recebido")
                    )

                    id_pedido = cursor.fetchone()[0]

                    for id_produto, quantidade, subtotal in precos_itens:
                        cursor.execute(
                            """
                            INSERT INTO Item_Pedido
                                (id_pedido, id_produto, quantidade, subtotal)
                            VALUES (%s, %s, %s, %s)
                            """,
                            (id_pedido, id_produto, quantidade, subtotal)
                        )

                    cursor.execute(
                        """
                        INSERT INTO Pagamento
                            (id_pedido, tipo_pagamento, valor, status_pagamento)
                        VALUES (%s, %s, %s, %s)
                        """,
                        (id_pedido, tipo_pagamento, valor_total, "Pendente")
                    )

                    if endereco:
                        cursor.execute(
                            """
                            INSERT INTO Entrega
                                (id_pedido, endereco, status_entrega)
                            VALUES (%s, %s, %s)
                            """,
                            (id_pedido, endereco, "Em preparo")
                        )

                    conexao.commit()
                    return redirect(url_for("listar_pedidos"))

    except Exception as erro_banco:
        if conexao:
            conexao.rollback()
        erro = f"Não foi possível criar o pedido: {erro_banco}"

    finally:
        if conexao:
            conexao.close()

    return render_template(
        "pedido_form.html",
        clientes=clientes,
        produtos=produtos,
        erro=erro
    )

if __name__ == "__main__":
    debug_local = os.getenv("FLASK_DEBUG", "0") == "1"
    app.run(debug=debug_local)

