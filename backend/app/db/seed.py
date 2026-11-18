"""Script de Povoamento de Dados Sintéticos Coerentes — DataMind AI
Gera uma base empresarial realista no SQLite para simulação de BI:
- 100 Clientes
- 22 Produtos em 6 categorias
- 5 Vendedores com metas mensais
- ~1.000 Vendas nos últimos 6 meses
- Itens de venda coerentes
- Contas a receber consistentes com casos de inadimplência real
"""

import sys
import random
from pathlib import Path
from datetime import datetime, date, timedelta

# Importa o gerenciador de banco
from database import init_db, get_write_connection, DB_PATH

# Fixar semente para reprodutibilidade dos testes
random.seed(42)

NOMES_PRIMEIROS = [
    "Lucas", "Beatriz", "Gabriel", "Mariana", "Rodrigo", "Camila", "Matheus", "Larissa",
    "Felipe", "Juliana", "Thiago", "Fernanda", "Bruno", "Amanda", "Gustavo", "Carolina",
    "Rafael", "Patricia", "Leonardo", "Aline", "Marcelo", "Renata", "Diego", "Bruna",
    "André", "Vanessa", "Vinicius", "Daniela", "Eduardo", "Jessica", "Alexandre", "Priscila"
]

SOBRENOMES = [
    "Silva", "Santos", "Oliveira", "Souza", "Rodrigues", "Ferreira", "Alves", "Pereira",
    "Lima", "Gomes", "Costa", "Ribeiro", "Martins", "Carvalho", "Almeida", "Lopes",
    "Soares", "Fernandes", "Vieira", "Barbosa", "Rocha", "Dias", "Nascimento", "Andrade"
]

CIDADES_ESTADOS = [
    ("São Paulo", "SP"), ("Campinas", "SP"), ("Santos", "SP"), ("Ribeirão Preto", "SP"),
    ("Rio de Janeiro", "RJ"), ("Niterói", "RJ"),
    ("Belo Horizonte", "MG"), ("Uberlândia", "MG"),
    ("Curitiba", "PR"), ("Londrina", "PR"),
    ("Porto Alegre", "RS"), ("Caxias do Sul", "RS"),
    ("Florianópolis", "SC"), ("Joinville", "SC"),
    ("Salvador", "BA"), ("Brasília", "DF"), ("Goiânia", "GO"), ("Recife", "PE")
]

PRODUTOS_CATALOGO = [
    # Hardware
    ("Notebook Pro 16 Intel i7", "Hardware", 7490.00, 35),
    ("Notebook Slim 14 Ryzen 7", "Hardware", 4250.00, 50),
    ("Desktop Corporate Core i5", "Hardware", 3800.00, 40),
    ("Servidor Rack 1U Xeon", "Hardware", 14500.00, 12),
    # Monitores
    ("Monitor UltraWide 34 IPS", "Monitores", 2399.00, 45),
    ("Monitor 27 4K HDR", "Monitores", 1850.00, 60),
    ("Monitor 24 FHD 75Hz", "Monitores", 890.00, 95),
    # Periféricos
    ("Teclado Mecânico RGB Pro", "Periféricos", 380.00, 120),
    ("Mouse Ergonômico Sem Fio", "Periféricos", 240.00, 150),
    ("Headset USB Noise Cancelling", "Periféricos", 320.00, 110),
    ("Webcam 4K Ultra Wide", "Periféricos", 460.00, 80),
    ("Caixa de Som Bluetooth Desk", "Periféricos", 290.00, 70),
    # Redes
    ("Roteador Mesh Wi-Fi 6 Duo", "Redes", 680.00, 65),
    ("Switch Gigabit 24 Portas", "Redes", 1150.00, 30),
    ("Adaptador USB-C Multiport 8 em 1", "Redes", 195.00, 140),
    # Armazenamento
    ("SSD NVMe 2TB PCIe 4.0", "Armazenamento", 850.00, 90),
    ("SSD NVMe 1TB PCIe 4.0", "Armazenamento", 480.00, 130),
    ("HD Externo 4TB Resistente", "Armazenamento", 620.00, 55),
    # Ergonomia & Móveis
    ("Cadeira Ergonômica Mesh", "Ergonomia", 1650.00, 40),
    ("Suporte Articulado Pistão a Gás", "Ergonomia", 185.00, 110),
    ("Mesa com Regulagem Elétrica", "Ergonomia", 2200.00, 25),
    ("Luminária Inteligente de Mesa", "Ergonomia", 175.00, 85),
]

VENDEDORES_CATALOGO = [
    ("Carlos Mendes", "carlos.mendes@empresa.com", 80000.00),
    ("Beatriz Souza", "beatriz.souza@empresa.com", 75000.00),
    ("Rafael Costa", "rafael.costa@empresa.com", 90000.00),
    ("Juliana Lima", "juliana.lima@empresa.com", 70000.00),
    ("Lucas Ferreira", "lucas.ferreira@empresa.com", 85000.00),
]


def popular_banco(reset: bool = True):
    print("Iniciando processo de povoamento do DataMind AI...")
    if reset and DB_PATH.exists():
        print(f"Limpando base existente: {DB_PATH}")
        try:
            DB_PATH.unlink()
        except Exception as e:
            print(f"Aviso ao remover banco existente: {e}")

    init_db()
    conn = get_write_connection()
    cursor = conn.cursor()

    # 1. Inserir Vendedores
    print("Cadastrando 5 vendedores comerciais...")
    vendedor_ids = []
    for nome, email, meta in VENDEDORES_CATALOGO:
        cursor.execute(
            "INSERT INTO vendedores (nome, email, meta_mensal) VALUES (?, ?, ?)",
            (nome, email, meta)
        )
        vendedor_ids.append(cursor.lastrowid)

    # 2. Inserir Produtos
    print("Cadastrando 22 produtos em 6 categorias...")
    produtos_data = []
    for nome, cat, preco, est in PRODUTOS_CATALOGO:
        cursor.execute(
            "INSERT INTO produtos (nome, categoria, preco, estoque) VALUES (?, ?, ?, ?)",
            (nome, cat, preco, est)
        )
        produtos_data.append({"id": cursor.lastrowid, "nome": nome, "preco": preco, "categoria": cat})

    # 3. Inserir 100 Clientes
    print("Gerando 100 clientes realistas...")
    cliente_ids = []
    hoje = datetime.now()
    emails_usados = set()

    for i in range(100):
        nome = f"{random.choice(NOMES_PRIMEIROS)} {random.choice(SOBRENOMES)}"
        base_email = nome.lower().replace(" ", ".")
        email = f"{base_email}{i+1}@exemplo.com.br"
        cidade, estado = random.choice(CIDADES_ESTADOS)
        dias_cadastro = random.randint(30, 365)
        data_cad = (hoje - timedelta(days=dias_cadastro)).strftime("%Y-%m-%d %H:%M:%S")

        cursor.execute(
            "INSERT INTO clientes (nome, email, cidade, estado, data_cadastro) VALUES (?, ?, ?, ?, ?)",
            (nome, email, cidade, estado, data_cad)
        )
        cliente_ids.append(cursor.lastrowid)

    # 4. Gerar 1.000 Vendas nos últimos 180 dias
    print("Gerando 1.000 vendas nos últimos 6 meses com itens e contas a receber...")
    status_opcoes = ["concluida"] * 88 + ["pendente"] * 7 + ["cancelada"] * 5

    contas_geradas = 0
    itens_gerados = 0

    for _ in range(1000):
        c_id = random.choice(cliente_ids)
        v_id = random.choice(vendedor_ids)
        dias_atras = random.randint(0, 180)
        data_venda = (hoje - timedelta(days=dias_atras, hours=random.randint(0, 23), minutes=random.randint(0, 59)))
        status_venda = random.choice(status_opcoes)

        cursor.execute(
            "INSERT INTO vendas (cliente_id, vendedor_id, data_venda, status) VALUES (?, ?, ?, ?)",
            (c_id, v_id, data_venda.strftime("%Y-%m-%d %H:%M:%S"), status_venda)
        )
        venda_id = cursor.lastrowid

        # 1 a 4 itens por venda
        num_itens = random.choices([1, 2, 3, 4], weights=[45, 30, 15, 10])[0]
        produtos_escolhidos = random.sample(produtos_data, num_itens)
        
        valor_total_venda = 0.0
        for prod in produtos_escolhidos:
            qtd = random.choices([1, 2, 3, 5], weights=[60, 25, 10, 5])[0]
            preco_unit = prod["preco"]
            valor_total_venda += qtd * preco_unit

            cursor.execute(
                "INSERT INTO itens_venda (venda_id, produto_id, quantidade, preco_unitario) VALUES (?, ?, ?, ?)",
                (venda_id, prod["id"], qtd, preco_unit)
            )
            itens_gerados += 1

        # Gerar Contas a Receber se não for cancelada
        if status_venda != "cancelada":
            # 1 ou 2 parcelas
            num_parcelas = 2 if valor_total_venda > 4000 else 1
            valor_parcela = round(valor_total_venda / num_parcelas, 2)

            for p in range(num_parcelas):
                prazo_dias = 30 * (p + 1)
                data_venc = (data_venda + timedelta(days=prazo_dias)).date()
                
                # Regra de inadimplência coerente:
                if data_venc < hoje.date():
                    # Venceu no passado: ~86% foram pagas, ~14% estão em inadimplência
                    inadimplente = (random.random() < 0.14)
                    if inadimplente:
                        status_pg = "pendente"
                        data_pg = None
                    else:
                        status_pg = "pago"
                        dias_pagto = random.randint(-5, 2) # pagou perto do vencimento
                        data_pg = (data_venc + timedelta(days=dias_pagto)).strftime("%Y-%m-%d")
                else:
                    # Vencimento futuro: conta pendente normal (a vencer)
                    status_pg = "pendente"
                    data_pg = None

                cursor.execute(
                    """
                    INSERT INTO contas_receber 
                    (cliente_id, venda_id, valor, vencimento, status_pagamento, data_pagamento)
                    VALUES (?, ?, ?, ?, ?, ?)
                    """,
                    (c_id, venda_id, valor_parcela, data_venc.strftime("%Y-%m-%d"), status_pg, data_pg)
                )
                contas_geradas += 1

    conn.commit()
    conn.close()

    print("\nPovoamento concluído com sucesso!")
    print(f"Total de Vendedores: {len(vendedor_ids)}")
    print(f"Total de Clientes: {len(cliente_ids)}")
    print(f"Total de Produtos: {len(produtos_data)}")
    print(f"Total de Vendas: 1000")
    print(f"Total de Itens de Venda: {itens_gerados}")
    print(f"Total de Títulos em Contas a Receber: {contas_geradas}")


if __name__ == "__main__":
    popular_banco()
