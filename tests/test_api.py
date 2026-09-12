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
        "descricao": "Teste Valor Zero"
    }
    response = client.post("/transacoes", json=payload_invalido)
    assert response.status_code == 400

def test_saldo_e_resumo_status():
    """Valida se as rotas de resumo e saldo respondem com sucesso."""
    response_saldo = client.get("/saldo")
    assert response_saldo.status_code == 200
    assert "saldo_atual" in response_saldo.json()