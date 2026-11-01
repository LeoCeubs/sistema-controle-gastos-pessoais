import asyncio
from fastapi import Request
from fastapi.testclient import TestClient
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.main import app, erro_http

client = TestClient(app)


def test_infraestrutura_lifespan_health_e_handler_204():
    """Cobre lifespan (linhas 18-19), /health (linha 59) e erro_http 204 (linha 47) do main.py."""
    with TestClient(app) as c:
        res = c.get("/health")
        assert res.status_code == 200
        assert res.json() == {"status": "ok"}

    # Cobre a linha 47 do handler erro_http quando status_code == 204
    scope = {"type": "http", "method": "GET", "path": "/", "headers": []}
    req = Request(scope)
    exc = StarletteHTTPException(status_code=204, detail=None)
    resp = asyncio.run(erro_http(req, exc))
    assert resp.status_code == 204


def test_criar_listar_editar_e_excluir_categorias_completo():
    """Cobre CRUD completo e casos de borda de categorias.py (linhas 16, 21-24, 52-60, 66-75)."""
    # 1. Criar e listar categorias
    res_post = client.post("/categorias", json={"nome": "Lazer e Viagens"})
    assert res_post.status_code in [201, 400]

    res_list = client.get("/categorias")
    assert res_list.status_code == 200
    categorias = res_list.json()
    assert isinstance(categorias, list)
    assert len(categorias) > 0

    # 2. Criar categorias específicas para testar atualização e exclusão (PUT e DELETE)
    res_cat1 = client.post("/categorias", json={"nome": "Cat Temp 1"})
    cat1_id = res_cat1.json()["id"]
    res_cat2 = client.post("/categorias", json={"nome": "Cat Temp 2"})
    cat2_id = res_cat2.json()["id"]

    # PUT com sucesso (linhas 16, 21-24, 52-60)
    res_put_ok = client.put(f"/categorias/{cat1_id}", json={"nome": "Cat Temp 1 Editada"})
    assert res_put_ok.status_code == 200
    assert res_put_ok.json()["nome"] == "Cat Temp 1 Editada"

    # PUT com nome duplicado de outra categoria (linha 55 -> 400)
    res_put_dup = client.put(f"/categorias/{cat1_id}", json={"nome": "Cat Temp 2"})
    assert res_put_dup.status_code == 400

    # PUT e DELETE em categoria inexistente (linha 23 -> 404)
    assert client.put("/categorias/999999", json={"nome": "Inexistente"}).status_code == 404
    assert client.delete("/categorias/999999").status_code == 404

    # DELETE de categoria em uso por transação (linhas 68-72 -> RN05 400)
    res_tx = client.post(
        "/transacoes",
        json={
            "valor": 50.0,
            "data": "2026-10-10",
            "tipo": "despesa",
            "categoria_id": cat1_id,
            "descricao": "Vínculo RN05",
        },
    )
    tx_id = res_tx.json()["id"]

    res_del_em_uso = client.delete(f"/categorias/{cat1_id}")
    assert res_del_em_uso.status_code == 400

    # Remove a transação e exclui as categorias temporárias com sucesso (linhas 74-75 -> 204)
    client.delete(f"/transacoes/{tx_id}")
    assert client.delete(f"/categorias/{cat1_id}").status_code == 204
    assert client.delete(f"/categorias/{cat2_id}").status_code == 204


def test_caso_de_borda_categoria_duplicada():
    """Caso de borda: Tentar cadastrar categoria com nome duplicado (RN04)."""
    payload = {"nome": "Alimentação"}
    client.post("/categorias", json=payload)

    response = client.post("/categorias", json={"nome": "alimentação"})
    assert response.status_code == 400
    data = response.json()
    mensagem = data.get("erro") or data.get("detail") or str(data)
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
    """Valida se as rotas de resumo (com e sem filtro de mês/ano) e saldo respondem com sucesso."""
    client.post("/categorias", json={"nome": "Salário"})
    cat_id = client.get("/categorias").json()[0]["id"]

    client.post(
        "/transacoes",
        json={
            "valor": 1000.0,
            "data": "2026-10-01",
            "tipo": "receita",
            "categoria_id": cat_id,
            "descricao": "Receita Teste Saldo",
        },
    )
    client.post(
        "/transacoes",
        json={
            "valor": 250.0,
            "data": "2026-10-02",
            "tipo": "despesa",
            "categoria_id": cat_id,
            "descricao": "Despesa Teste Saldo",
        },
    )

    response_saldo = client.get("/saldo")
    assert response_saldo.status_code == 200
    assert "saldo_atual" in response_saldo.json()

    # Cobre resumo sem filtros e com filtros mes e ano (linhas 18 e 20 de resumo.py)
    assert client.get("/resumo").status_code == 200
    res_filtrado = client.get("/resumo?mes=10&ano=2026")
    assert res_filtrado.status_code == 200
    assert "saldo_periodo" in res_filtrado.json()


def test_ciclo_completo_transacao_criar_editar_consultar_excluir():
    """Cenário principal: Cria, consulta, filtra por categoria, atualiza e exclui uma transação."""
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

    # Cobre a linha 27 de transacoes.py passando o query param 'categoria'
    res_filtro = client.get(f"/transacoes?mes=10&ano=2026&categoria={cat_id}")
    assert res_filtro.status_code == 200
    assert len(res_filtro.json()) >= 1

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
    mensagem = data.get("erro") or data.get("detail") or str(data)
    assert "categoria não encontrada" in mensagem.lower()


def test_caso_de_borda_consultar_editar_e_excluir_transacao_inexistente():
    """Caso de borda: Consultar, editar ou excluir transação com ID inexistente retorna 404."""
    assert client.get("/transacoes/999999").status_code == 404
    assert client.delete("/transacoes/999999").status_code == 404

    payload_editar = {
        "valor": 100.00,
        "data": "2026-10-15",
        "tipo": "despesa",
        "categoria_id": 1,
        "descricao": "Edição Inexistente",
    }
    assert client.put("/transacoes/999999", json=payload_editar).status_code == 404


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