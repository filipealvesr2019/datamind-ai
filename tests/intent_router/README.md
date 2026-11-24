# Testes do Intent Router (`test_intent_router.py`)

Valida o roteador de intenções em `backend/app/agent/intent_router.py`, responsável por classificar intenções, detectar ambiguidades e consolidar o histórico do chat.

## Cenários Cobertos

- **`test_formatar_historico_vazio`**: Garante tratamento seguro quando o histórico é `None` ou lista vazia.
- **`test_formatar_historico_com_mensagens`**: Verifica formatação correta de mensagens de `user` e `assistant`.
- **`test_modelo_intent_decision`**: Valida o schema Pydantic `IntentDecision` para casos de esclarecimento.
- **`test_fallback_seguro_sem_modelos_validos`**: Garante que, mesmo sem modelos disponíveis, o roteador retorna fallback seguro para `consulta_dados` sem quebrar o chat.

## Como Executar

```bash
python -m unittest tests/intent_router/test_intent_router.py -v
```
