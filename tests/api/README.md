# Testes de Integração da API (`test_api.py`)

Valida os endpoints HTTP da aplicação FastAPI em `backend/app/main.py` utilizando `TestClient`.

## Cenários Cobertos

- **`test_kpis_dashboard`**: Verifica `GET /api/kpis` (`200 OK`) e presença de `faturamento_total`, `vendas_concluidas`, `ticket_medio` e `inadimplencia_total`.
- **`test_vendas_mensais`**: Verifica `GET /api/dashboard/vendas-mensais` retornando lista mensal com `mes` e `faturamento`.
- **`test_top_produtos`**: Verifica `GET /api/dashboard/top-produtos` retornando exatamente 5 produtos.
- **`test_audit_endpoint`**: Verifica `GET /api/audit?limite=5` retornando lista de logs de auditoria.
- **`test_export_pdf_endpoint`**: Verifica `POST /api/export/pdf` retornando `application/pdf` válido (`%PDF-`) e valida o texto extraído com `pypdf`.
- **`test_export_pdf_rejeita_vazio`**: Garante retorno `400 Bad Request` quando o conteúdo do relatório está vazio.
- **`test_chat_rejeita_pergunta_vazia`**: Garante retorno `400 Bad Request` quando `pergunta` está vazia.
- **`test_frontend_estatico_e_funcoes_exportacao`**: Verifica `GET /` e `GET /js/app.js`, confirmando presença de `exportarPDF`, `exportarCSV` e `exportarPNG`.

## Como Executar

```bash
python -m unittest tests/api/test_api.py -v
```
