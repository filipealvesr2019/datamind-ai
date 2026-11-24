# Testes da Camada de Segurança SQL (`test_security.py`)

Valida o analisador de AST (`sqlglot`) em `backend/app/security/sql_guard.py`, que impede mutações e injeções SQL.

## Cenários Cobertos

- **`test_select_valido_injeta_limit_padrao`**: Garante injeção automática de `LIMIT 100` em consultas `SELECT` sem limite.
- **`test_limit_excessivo_e_limitado_ao_teto`**: Garante que limites acima do permitido sejam reduzidos para `LIMIT 500`.
- **`test_bloqueia_drop_table`**: Garante bloqueio de `DROP TABLE` com `SQLValidationError`.
- **`test_bloqueia_delete`**: Garante bloqueio de `DELETE` com `SQLValidationError`.
- **`test_bloqueia_multiplas_instrucoes`**: Garante bloqueio de múltiplas instruções separadas por `;`.
- **`test_bloqueia_tabela_nao_autorizada`**: Garante whitelisting estrito, bloqueando acesso a tabelas fora do catálogo (ex.: `sqlite_master`).

## Como Executar

```bash
python -m unittest tests/sql_security/test_security.py -v
```
