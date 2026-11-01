# Parte 2: Refinamento por Testes, Erros Lógicos e Re-especificação

## 2.1 Resultados dos Testes Automatizados (Test Harness)
A suíte de testes automatizados (`tests/test_api.py`) foi expandida e executada no ambiente padronizado (Docker) utilizando `pytest` e `TestClient` do FastAPI, cobrindo integralmente os cenários principais (CRUD de categorias e transações, cálculo de saldo, listagem com filtros e exportação CSV) e os casos de borda (*edge cases*), atingindo **100% de aprovação (9/9 testes passando)**.

### Comando de Execução no Ambiente Padronizado:
```bash
docker compose run --rm --build api python -m pytest -v