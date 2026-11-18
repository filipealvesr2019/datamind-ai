# DataMind AI — Analista Empresarial Inteligente (BI + Agente de IA)

O **DataMind AI** é uma plataforma SaaS de Business Intelligence com um Agente de Inteligência Artificial integrado (Google Gemini + LangChain). Ele permite que gestores conversem com a base de dados corporativa em linguagem natural, obtendo indicadores, respostas explicativas, gráficos interativos (Plotly) e visualização transparente do SQL executado com governança e segurança cibernética corporativa.

---

## 🚀 Arquitetura e Diferenciais Técnicos

1. **Camada Intermediária de Segurança (AST Parser)**:
   - Validação da Árvore Sintática com `sqlglot`: aceita unicamente instruções `SELECT`.
   - Bloqueio terminante de mutações (`INSERT`, `UPDATE`, `DELETE`, `DROP`, `ALTER`).
   - Whitelisting de tabelas e injeção automática de cláusula `LIMIT 100`.
2. **Conexões Desacopladas no SQLite**:
   - **Conexão Analítica**: Modo estritamente somente leitura (`file:empresa.db?mode=ro`). O driver do SQLite impede qualquer gravação a nível de sistema operacional.
   - **Conexão de Auditoria**: Conexão isolada que registra em tempo real todas as consultas (aprovadas, bloqueadas e erros de execução).
3. **Gráficos Determinísticos**:
   - O LLM não precisa alucinar código JSON. O agente identifica o tipo de gráfico e as variáveis; o backend monta deterministamente a especificação Plotly.js.
4. **Interface Moderna (SaaS de BI)**:
   - Dashboard de KPIs com faturamento, ticket médio e taxa de inadimplência real.
   - Página dedicada para o Analista IA com histórico, sugestões rápidas e acordeão de transparência SQL.
   - Tela de auditoria e governança de dados em tempo real.

---

## 🛠️ Tecnologias Utilizadas

- **Linguagem**: Python 3.14+
- **LLM / Agente**: Google Gemini (`gemini-2.5-flash`), LangChain, `langchain-google-genai`
- **Segurança SQL**: `sqlglot` (análise de AST)
- **Banco de Dados**: SQLite (com schema normalizado e índices analíticos)
- **Backend**: FastAPI + Uvicorn + Pydantic
- **Frontend**: HTML5, Tailwind CSS, Lucide Icons, Plotly.js, Marked.js

---

## 📂 Estrutura de Pastas

```
datamind-ai/
├── backend/
│   ├── app/
│   │   ├── agent/
│   │   │   ├── engine.py           # Agente LangChain + Gemini com tool calling
│   │   │   └── prompt.py           # System Prompt com regras estritas de negócio
│   │   ├── db/
│   │   │   ├── database.py         # Conexões Read-Only e Auditoria
│   │   │   ├── schema.sql          # DDL das 6 tabelas + índices
│   │   │   └── seed.py             # Gerador sintético realista (1.000 vendas)
│   │   ├── security/
│   │   │   └── sql_guard.py        # Validador de AST (sqlglot) e whitelisting
│   │   ├── services/
│   │   │   └── chart_builder.py    # Construtor determinístico de gráficos Plotly
│   │   └── main.py                 # Servidor e rotas da API FastAPI
│   ├── tests/
│   │   ├── test_db.py              # Teste de KPIs e integridade relacional
│   │   ├── test_security.py        # Teste de invasão, DROP, DELETE e injeções
│   │   └── test_agent.py           # Teste das 5 perguntas essenciais do agente
│   ├── .env.example
│   ├── .env
│   └── requirements.txt
├── data/
│   └── empresa.db                  # Banco de dados populado
├── frontend/
│   ├── index.html                  # Interface do Dashboard e Analista IA
│   └── js/
│       └── app.js                  # Lógica do frontend e renderização Plotly
├── run.py                          # Ponto de entrada da aplicação
└── README.md
```

---

## ⚡ Como Executar o Projeto

### 1. Clonar e Instalar Dependências
```bash
pip install -r backend/requirements.txt
```

### 2. Configurar a Chave da API do Gemini
Crie ou edite o arquivo `backend/.env`:
```ini
GEMINI_API_KEY=sua_chave_aqui
GEMINI_MODEL=gemini-2.5-flash
```
*(Obtenha uma chave gratuita em: https://aistudio.google.com/)*

### 3. Povoar o Banco de Dados (Seed)
```bash
cd backend/app/db
python seed.py
```

### 4. Rodar os Testes Automatizados
```bash
python backend/tests/test_db.py
python backend/tests/test_security.py
python backend/tests/test_agent.py
```

### 5. Iniciar a Aplicação Web
```bash
python run.py
```
Acesse no navegador: **http://127.0.0.1:8080**

---

## 🎯 Roteiro de Demonstração para Entrevistas Técnicas

1. **Demonstrar o Dashboard**:
   - Mostrar os 4 KPIs em tempo real (Faturamento de R$ 6M+, volume de vendas e inadimplência real calculada apenas sobre títulos vencidos).
   - Mostrar a evolução mensal e o gráfico dos produtos mais vendidos.
2. **Demonstrar o Analista IA**:
   - Fazer uma pergunta: *"Quais foram os cinco produtos mais vendidos em quantidade e gere um gráfico de barras?"*.
   - Destacar como a IA monta a query SQL segura, aciona o construtor do gráfico e exibe a transparência técnica na tela.
3. **Demonstrar a Camada de Segurança**:
   - Tentar fazer uma pergunta perigosa no chat: *"Apague a tabela de clientes"*.
   - Mostrar o bloqueio imediato pelo validador AST (`sqlglot`), sem jamais tocar o banco de dados.
4. **Demonstrar a Auditoria**:
   - Abrir a aba **Auditoria & SQL** e mostrar o registro da consulta aprovada e do bloqueio efetuado.
