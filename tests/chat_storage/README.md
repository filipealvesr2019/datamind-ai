# Testes de Persistência de Conversas (`test_chat_storage.py`)

Valida o serviço `backend/app/services/chat_storage.py`, responsável por salvar, listar, carregar e excluir conversas e mensagens (incluindo gráficos Plotly e dados tabulares) no SQLite.

## Cenários Cobertos

- **`test_criar_e_listar_conversas`**: Verifica criação de conversa e listagem ordenada.
- **`test_salvar_mensagens_e_titulo_automatico`**: Verifica persistência de mensagens de usuário e assistente com gráfico/tabela JSON e atualização automática do título com a primeira pergunta.
- **`test_excluir_conversa_remove_em_cascata`**: Verifica exclusão da conversa e retorno `None` ao tentar carregá-la novamente.
- **`test_obter_conversa_inexistente_retorna_none`**: Garante retorno `None` para IDs inexistentes.

## Como Executar

```bash
python -m unittest tests/chat_storage/test_chat_storage.py -v
```
