-- Schema do Banco de Dados Empresarial - DataMind AI
-- Arquivo: schema.sql

PRAGMA foreign_keys = ON;

-- 1. Clientes
CREATE TABLE IF NOT EXISTS clientes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nome TEXT NOT NULL,
    email TEXT NOT NULL UNIQUE,
    cidade TEXT NOT NULL,
    estado TEXT NOT NULL,
    data_cadastro TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- 2. Produtos
CREATE TABLE IF NOT EXISTS produtos (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nome TEXT NOT NULL,
    categoria TEXT NOT NULL,
    preco REAL NOT NULL,
    estoque INTEGER NOT NULL DEFAULT 0
);

-- 3. Vendedores
CREATE TABLE IF NOT EXISTS vendedores (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nome TEXT NOT NULL,
    email TEXT NOT NULL,
    meta_mensal REAL NOT NULL DEFAULT 50000.0
);

-- 4. Vendas
CREATE TABLE IF NOT EXISTS vendas (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    cliente_id INTEGER NOT NULL REFERENCES clientes(id),
    vendedor_id INTEGER NOT NULL REFERENCES vendedores(id),
    data_venda TIMESTAMP NOT NULL,
    status TEXT NOT NULL CHECK(status IN ('concluida', 'cancelada', 'pendente'))
);

-- 5. Itens da Venda
CREATE TABLE IF NOT EXISTS itens_venda (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    venda_id INTEGER NOT NULL REFERENCES vendas(id) ON DELETE CASCADE,
    produto_id INTEGER NOT NULL REFERENCES produtos(id),
    quantidade INTEGER NOT NULL,
    preco_unitario REAL NOT NULL
);

-- 6. Contas a Receber
CREATE TABLE IF NOT EXISTS contas_receber (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    cliente_id INTEGER NOT NULL REFERENCES clientes(id),
    venda_id INTEGER NOT NULL REFERENCES vendas(id),
    valor REAL NOT NULL,
    vencimento DATE NOT NULL,
    status_pagamento TEXT NOT NULL CHECK(status_pagamento IN ('pago', 'pendente')),
    data_pagamento DATE
);

-- 7. Tabela de Auditoria e Logs do Agente
CREATE TABLE IF NOT EXISTS auditoria_consultas (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    data_hora TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    pergunta_usuario TEXT,
    sql_proposto TEXT NOT NULL,
    status TEXT NOT NULL CHECK(status IN ('APROVADO', 'BLOQUEADO', 'ERRO_EXECUCAO')),
    motivo_bloqueio TEXT,
    tempo_execucao_ms REAL,
    linhas_retornadas INTEGER
);

-- Índices Analíticos de Alta Performance
CREATE INDEX IF NOT EXISTS idx_vendas_data ON vendas(data_venda);
CREATE INDEX IF NOT EXISTS idx_vendas_status ON vendas(status);
CREATE INDEX IF NOT EXISTS idx_vendas_cliente ON vendas(cliente_id);
CREATE INDEX IF NOT EXISTS idx_vendas_vendedor ON vendas(vendedor_id);
CREATE INDEX IF NOT EXISTS idx_itens_venda_venda ON itens_venda(venda_id);
CREATE INDEX IF NOT EXISTS idx_itens_venda_produto ON itens_venda(produto_id);
CREATE INDEX IF NOT EXISTS idx_contas_receber_status_venc ON contas_receber(status_pagamento, vencimento);
CREATE INDEX IF NOT EXISTS idx_contas_receber_cliente ON contas_receber(cliente_id);
