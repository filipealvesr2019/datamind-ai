# Testes do Exportador de PDF (`test_pdf_exporter.py`)

Valida o gerador de relatórios executivos em `backend/app/services/pdf_exporter.py` (ReportLab + Pillow + validação com `pypdf`).

## Cenários Cobertos

- **`test_gera_pdf_valido_com_texto_grafico_e_tabela`**: Gera um PDF completo contendo cabeçalho, pergunta, texto Markdown, imagem PNG em base64 e tabela de dados, verificando assinatura `%PDF-` e leitura do conteúdo via `PdfReader`.
- **`test_ignora_imagem_corrompida_sem_falhar`**: Garante resiliência caso a imagem base64 do gráfico venha corrompida, gerando o PDF normalmente com o restante do conteúdo.

## Como Executar

```bash
python -m unittest tests/pdf_exporter/test_pdf_exporter.py -v
```
