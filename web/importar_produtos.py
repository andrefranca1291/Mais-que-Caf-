from conexao import conectar


produtos = [
    ("CAFÉ EXPRESSO", "Café preparado sob pressão, servido em dose individual.", 3.50, "Bebidas Quentes"),
    ("CAPPUCCINO", "Café espresso com leite vaporizado e espuma cremosa.", 5.00, "Bebidas Quentes"),
    ("CHOCOLATE QUENTE", "Bebida cremosa de chocolate, servida quente.", 5.00, "Bebidas Quentes"),
    ("GUARANÁ", "Refrigerante de guaraná em lata de 350 ml.", 7.00, "Bebidas Frias"),
    ("GUARANÁ ZERO", "Refrigerante de guaraná zero em lata de 350 ml.", 7.00, "Bebidas Frias"),
    ("COCA COLA", "Refrigerante Coca-Cola em lata de 350 ml.", 7.00, "Bebidas Frias"),
    ("COCA ZERO", "Refrigerante Coca-Cola sem açúcar em lata de 350 ml.", 7.00, "Bebidas Frias"),
    ("PÃO DE QUEIJO", "Pão de queijo assado, servido quentinho.", 5.00, "Salgados"),
    ("ENROLADINHO DE QUEIJO", "Massa assada recheada com queijo.", 7.50, "Salgados"),
    ("COXINHA", "Salgado de massa macia recheado com frango.", 12.00, "Salgados"),
    ("ESFIRRA DE CARNE", "Massa assada recheada com carne temperada.", 10.50, "Salgados"),
    ("PÃO PIZZA", "Pão macio preparado com ingredientes de pizza.", 8.50, "Salgados"),
    ("RISOLE DE CARNE", "Salgado empanado recheado com carne temperada.", 12.00, "Salgados"),
    ("SANDUICHE NATURAL", "Sanduíche frio preparado com pão e recheio leve.", 13.00, "Salgados"),
    ("BROWNIE", "Brownie de chocolate recheado.", 8.00, "Doces"),
    ("BOLO NO POTE", "Bolo no pote de leite Ninho com Nutella.", 15.00, "Doces"),
]


conexao = None
cursor = None

try:
    conexao = conectar()
    cursor = conexao.cursor()

    inseridos = 0
    existentes = 0

    for nome, descricao, preco, categoria in produtos:
        cursor.execute(
            "SELECT id_produto FROM produto WHERE nome = %s LIMIT 1",
            (nome,)
        )

        if cursor.fetchone():
            existentes += 1
            continue

        cursor.execute(
            """
            INSERT INTO produto (nome, descricao, preco, categoria)
            VALUES (%s, %s, %s, %s)
            """,
            (nome, descricao, preco, categoria)
        )
        inseridos += 1

    conexao.commit()
    print(f"Importação concluída: {inseridos} produtos inseridos; {existentes} já existiam.")

except Exception as erro:
    if conexao:
        conexao.rollback()
    print(f"Erro ao importar produtos: {erro}")

finally:
    if cursor:
        cursor.close()
    if conexao:
        conexao.close()