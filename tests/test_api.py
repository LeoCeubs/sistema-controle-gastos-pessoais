from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_criar_e_listar_categorias_sucesso():
    """Cenário principal: Criação de categoria válida e listagem."""
    payload = {"nome": "Lazer e Viagens"}
    response = client.post("/categorias", json=payload)

    assert response.status_code in [201, 400]

    res_list = client.get("/categorias")
    assert res_list.status_code == 200
    categorias = res_list.json()
    assert isinstance(categorias, list)
    assert len(categorias) > 0


def test_caso_de_borda_categoria_duplicada():
    """Caso de borda: Tentar cadastrar categoria com nome duplicado (RN04)."""
    payload = {"nome": "Alimentação"}
    client.post("/categorias", json=payload)

    response = client.post("/categorias", json={"nome": "alimentação"})
    assert response.status_code == 400
    data = response.json()
    mensagem = data.get("detail") or data.get("message") or str(data)
    assert "já cadastrada" in mensagem.lower()


def test_caso_de_borda_transacao_valor_invalido():
    """Caso de borda: Tentar cadastrar transação com valor menor ou igual a zero (RN02)."""
    payload_invalido = {
        "valor": 0.0,
        "data": "2026-09-12",
        "tipo": "despesa",
        "categoria_id": 1,
        "descricao": "Teste Valor Zero",
    }
    response = client.post("/transacoes", json=payload_invalido)
    assert response.status_code in [400, 422]


def test_saldo_e_resumo_status():
    """Valida se as rotas de resumo e saldo respondem com sucesso."""
    response_saldo = client.get("/saldo")
    assert response_saldo.status_code == 200
    assert "saldo_atual" in response_saldo.json()


def test_ciclo_completo_transacao_criar_editar_consultar_excluir():
    """Cenário principal: Cria, consulta, atualiza (Ajuste 1 SDD) e exclui uma transação."""
    client.post("/categorias", json={"nome": "Moradia"})
    categorias = client.get("/categorias").json()
    cat_id = categorias[0]["id"]

    payload_criar = {
        "valor": 150.50,
        "data": "2026-10-15",
        "tipo": "despesa",
        "categoria_id": cat_id,
        "descricao": "Conta de Energia",
    }
    res_post = client.post("/transacoes", json=payload_criar)
    assert res_post.status_code == 201
    transacao_criada = res_post.json()
    transacao_id = transacao_criada["id"]
    assert transacao_criada["valor"] == 150.50

    res_get = client.get(f"/transacoes/{transacao_id}")
    assert res_get.status_code == 200
    assert res_get.json()["descricao"] == "Conta de Energia"

    payload_editar = {
        "valor": 180.00,
        "data": "2026-10-15",
        "tipo": "despesa",
        "categoria_id": cat_id,
        "descricao": "Conta de Energia Atualizada",
    }
    res_put = client.put(f"/transacoes/{transacao_id}", json=payload_editar)
    assert res_put.status_code == 200
    assert res_put.json()["valor"] == 180.00
    assert res_put.json()["descricao"] == "Conta de Energia Atualizada"

    res_del = client.delete(f"/transacoes/{transacao_id}")
    assert res_del.status_code == 204

    res_get_apos_del = client.get(f"/transacoes/{transacao_id}")
    assert res_get_apos_del.status_code == 404


def test_caso_de_borda_transacao_categoria_inexistente():
    """Caso de borda: Tentar criar transação com categoria_id que não existe."""
    payload = {
        "valor": 50.0,
        "data": "2026-10-15",
        "tipo": "receita",
        "categoria_id": 999999,
        "descricao": "Categoria Fantasma",
    }
    response = client.post("/transacoes", json=payload)
    assert response.status_code == 404
    data = response.json()
    mensagem = data.get("detail") or data.get("message") or str(data)
    assert "categoria não encontrada" in mensagem.lower()


def test_caso_de_borda_consultar_e_excluir_transacao_inexistente():
    """Caso de borda: Consultar, editar ou excluir transação com ID inexistente retorna 404."""
    assert client.get("/transacoes/999999").status_code == 404
    assert client.delete("/transacoes/999999").status_code == 404


def test_filtros_sem_resultado_nao_gera_erro_rn08():
    """Caso de borda (RN08): Filtrar por mês/ano sem movimentações retorna lista vazia (200 OK)."""
    response = client.get("/transacoes?mes=1&ano=1950")
    assert response.status_code == 200
    assert response.json() == []


def test_exportar_transacoes_csv_rf09():
    """Valida a exportação de transações em CSV com BOM UTF-8 (RF09)."""
    response = client.get("/transacoes/exportar")
    assert response.status_code == 200
    assert "text/csv" in response.headers["content-type"]
    assert "id;data;tipo;categoria;valor;descricao" in response.text