# Documento de Evidências de Execução

**Projeto:** Sistema de Controle de Gastos Pessoais
**Escopo deste documento:** item 3 da Entrega 1 — Ambiente Padronizado e Agentes de IA (issue #3)
**Responsável:** Bhrenno Almeida Borges
**Data da execução:** 12/09/2026
**Ambiente:** Windows 11 · Docker 29.1.2 · Docker Compose v2.40.3

Todas as saídas abaixo foram copiadas diretamente do terminal durante a execução real, com o
volume do banco apagado antes do início, para que a sequência pudesse ser reproduzida do zero.

---

## 1. Reprodutibilidade do ambiente (RNF03, RNF04)

### 1.1 Versões

```console
$ docker --version
Docker version 29.1.2, build 890dcca

$ docker compose version
Docker Compose version v2.40.3-desktop.1
```

### 1.2 Subida a partir do zero

```console
$ docker compose down -v
 Volume sistemadecontroledegastospessoais_dados  Removing
 Volume sistemadecontroledegastospessoais_dados  Removed
 Network sistemadecontroledegastospessoais_default  Removed

$ docker compose up --build -d
 Volume sistemadecontroledegastospessoais_dados  Created
 Container gastos-api  Creating
 Container gastos-api  Created
 Container gastos-api  Starting
 Container gastos-api  Started

$ docker compose ps
NAME         STATUS         PORTS
gastos-api   Up 9 seconds   0.0.0.0:8000->8000/tcp, [::]:8000->8000/tcp

$ docker compose logs api
INFO:     Uvicorn running on http://0.0.0.0:8000 (Press CTRL+C to quit)
INFO:     Started reloader process [1] using WatchFiles
INFO:     Started server process [8]
INFO:     Waiting for application startup.
INFO:     Application startup complete.
```

**Resultado:** ambiente sobe com um único comando, sem instalação de Python no host.

---

## 2. Infraestrutura e carga inicial

| Verificação | Comando | Resultado |
|---|---|---|
| Serviço no ar | `GET /health` | `200` |
| Categorias padrão (RN06) | `GET /categorias` | `200` com 3 registros |

```console
$ curl http://localhost:8000/health
  -> HTTP 200 {"status":"ok"}

$ curl http://localhost:8000/categorias
  -> HTTP 200 [{"id":1,"nome":"Alimentação"},{"id":2,"nome":"Salário"},{"id":3,"nome":"Outros"}]
```

**Resultado:** a RN06 é cumprida — o sistema não inicia vazio, e as três categorias são
editáveis e removíveis.

---

## 3. Cenários principais

```console
$ curl -X POST /transacoes   (receita — RF01)
  -> HTTP 201 {"id":1,"valor":3200.0,"data":"2026-09-05","tipo":"receita","categoria_id":2,
               "categoria":{"id":2,"nome":"Salário"},"descricao":"Salario de setembro"}

$ curl -X POST /transacoes   (despesa — RF01)
  -> HTTP 201 {"id":2,"valor":150.5,"data":"2026-09-10","tipo":"despesa","categoria_id":1,
               "categoria":{"id":1,"nome":"Alimentação"},"descricao":"Compra no mercado"}

$ curl -X POST /categorias   (categoria personalizada — RF02)
  -> HTTP 201 {"id":4,"nome":"Transporte"}

$ curl -X PUT /transacoes/1  (edição — Ajuste 1 da SDD)
  -> HTTP 200 {"id":1,"valor":3300.0,"data":"2026-09-05","tipo":"receita","categoria_id":2,
               "categoria":{"id":2,"nome":"Salário"},"descricao":"Salario de setembro (corrigido)"}

$ curl "/transacoes?mes=9&ano=2026"   (RF03, RF05)
  -> HTTP 200 [{"id":2,"valor":150.5,...,"categoria":{"id":1,"nome":"Alimentação"},...},
               {"id":1,"valor":3300.0,...,"categoria":{"id":2,"nome":"Salário"},...}]

$ curl /saldo                          (RF06)
  -> HTTP 200 {"saldo_atual":3149.5}

$ curl "/resumo?mes=9&ano=2026"        (RF07)
  -> HTTP 200 {"total_receitas":3300.0,"total_despesas":150.5,"saldo_periodo":3149.5}

$ curl -X DELETE /categorias/4         (RF02 — categoria sem vínculo)
  -> HTTP 204
```

**Conferência aritmética:** 3300,00 de receitas − 150,50 de despesas = 3149,50 de saldo. Os três
endpoints (`/saldo`, `/resumo` e a listagem) são consistentes entre si.

---

## 4. Casos de borda e regras de negócio

Esta é a seção mais importante do documento: cada regra da seção 3 da SDD foi exercitada com uma
entrada que deveria ser recusada, e verificou-se o **status HTTP** e a **mensagem** devolvidos.

| # | Regra | Entrada enviada | Esperado | Obtido | Situação |
|---|---|---|---|---|---|
| 1 | RN01 | `POST /transacoes` sem o campo `data` | 400 | `400 {"erro":"data: Field required"}` | ✅ |
| 2 | RN02 | `valor: 0` | 400 | `400 {"erro":"valor: Input should be greater than 0"}` | ✅ |
| 3 | RN02 | `valor: -50` | 400 | `400 {"erro":"valor: Input should be greater than 0"}` | ✅ |
| 4 | RN03 | `data: "2026-02-30"` | 400 | `400 {"erro":"data: ... day value is outside expected range"}` | ✅ |
| 5 | RN04 | `POST /categorias {"nome":"ALIMENTAÇÃO"}` | 400 | `400 {"erro":"Categoria já cadastrada."}` | ✅ |
| 6 | RN04 | `POST /categorias {"nome":"  alimentação  "}` | 400 | `400 {"erro":"Categoria já cadastrada."}` | ✅ |
| 7 | RN05 | `DELETE /categorias/1` com transação vinculada | 400 | `400 {"erro":"Categoria em uso."}` | ✅ |
| 8 | — | `GET /transacoes/999` | 404 | `404 {"erro":"Transação não encontrada."}` | ✅ |
| 9 | — | `PUT /categorias/999` | 404 | `404 {"erro":"Categoria não encontrada."}` | ✅ |
| 10 | RN08 | `GET /transacoes?mes=1&ano=1999` | 200 `[]` | `200 []` | ✅ |
| 11 | RN08 | `GET /resumo?mes=1&ano=1999` | totais zerados | `200 {"total_receitas":0.0,"total_despesas":0.0,"saldo_periodo":0.0}` | ✅ |
| 12 | RN07 | despesa de 9000 com saldo insuficiente | 201, saldo negativo permitido | `201` e `{"saldo_atual":-5850.5}` | ✅ |

Saídas literais:

```console
[RN01] POST /transacoes sem o campo data
  -> HTTP 400 {"erro":"data: Field required"}

[RN02] POST /transacoes com valor = 0
  -> HTTP 400 {"erro":"valor: Input should be greater than 0"}

[RN02] POST /transacoes com valor negativo
  -> HTTP 400 {"erro":"valor: Input should be greater than 0"}

[RN03] POST /transacoes com data 2026-02-30
  -> HTTP 400 {"erro":"data: Input should be a valid date or datetime, day value is outside expected range"}

[RN04] POST /categorias {"nome": "ALIMENTAÇÃO"}
  -> HTTP 400 {"erro":"Categoria já cadastrada."}

[RN04] POST /categorias {"nome": "  alimentação  "}
  -> HTTP 400 {"erro":"Categoria já cadastrada."}

[RN05] DELETE /categorias/1 (categoria vinculada a transação)
  -> HTTP 400 {"erro":"Categoria em uso."}

[404] GET /transacoes/999
  -> HTTP 404 {"erro":"Transação não encontrada."}

[404] PUT /categorias/999
  -> HTTP 404 {"erro":"Categoria não encontrada."}

[RN08] GET /transacoes?mes=1&ano=1999
  -> HTTP 200 []

[RN08] GET /resumo?mes=1&ano=1999
  -> HTTP 200 {"total_receitas":0.0,"total_despesas":0.0,"saldo_periodo":0.0}

[RN07] POST despesa de 9000 (saldo insuficiente)
  -> HTTP 201 {"id":3,"valor":9000.0,"data":"2026-09-12","tipo":"despesa","categoria_id":3,...}

[RN07] GET /saldo após a despesa
  -> HTTP 200 {"saldo_atual":-5850.5}
```

**Observações relevantes:**

- Os casos 1 a 4 comprovam o cumprimento do **RNF09**: sem os *exception handlers* de
  `app/main.py`, o FastAPI devolveria `422` com `{"detail":[...]}`. Nenhuma resposta vazou nesse
  formato.
- Os casos 5 e 6 comprovam que a comparação da RN04 é insensível a maiúsculas e ignora espaços
  nas bordas.
- O caso 12 comprova a RN07: o sistema **não** bloqueia despesa por saldo insuficiente; ele apenas
  reflete o saldo negativo, que representa dívida ou cheque especial.

---

## 5. Exportação de relatório em CSV (RF09)

```console
$ curl -D - "http://localhost:8000/transacoes/exportar?mes=9&ano=2026"
HTTP/1.1 200 OK
date: Sat, 12 Sep 2026 20:21:27 GMT
server: uvicorn
content-disposition: attachment; filename="relatorio_gastos.csv"
content-length: 236
content-type: text/csv; charset=utf-8

id;data;tipo;categoria;valor;descricao
1;2026-09-05;receita;Salário;3300.00;Salario de setembro (corrigido)
2;2026-09-10;despesa;Alimentação;150.50;Compra no mercado
3;2026-09-12;despesa;Outros;9000.00;Teste de saldo negativo
```

**Resultado:** cabeçalho `Content-Disposition` correto para download, arquivo nomeado
`relatorio_gastos.csv`, filtro de período aplicado e acentuação preservada. O CSV é gerado com o
módulo `csv` da biblioteca padrão, sem dependência externa.

---

## 6. Persistência dos dados em volume Docker (RNF02)

Este é o teste que comprova que o banco sobrevive à destruição do container.

```console
$ curl http://localhost:8000/saldo
{"saldo_atual":-5850.5}

$ docker compose down
 Container gastos-api  Removed
 Network sistemadecontroledegastospessoais_default  Removed

$ docker compose up -d
 Container gastos-api  Starting
 Container gastos-api  Started

$ curl http://localhost:8000/saldo
{"saldo_atual":-5850.5}

$ curl http://localhost:8000/transacoes
[{"id":3,"valor":9000.0,"data":"2026-09-12","tipo":"despesa","categoria_id":3,
  "categoria":{"id":3,"nome":"Outros"},"descricao":"Teste de saldo negativo"}, ...]
```

**Resultado:** o container foi removido e recriado, e os dados permaneceram intactos. É o volume
nomeado `dados`, declarado no `docker-compose.yml`, que garante esse comportamento.

---

## 7. Documentação automática da API (RNF08)

O Swagger é gerado pelo FastAPI a partir do próprio código, em `http://localhost:8000/docs`.
Levantamento dos endpoints publicados no `openapi.json`:

```console
$ curl http://localhost:8000/openapi.json

GET    /categorias                  tags=['Categorias']
POST   /categorias                  tags=['Categorias']
PUT    /categorias/{categoria_id}   tags=['Categorias']
DELETE /categorias/{categoria_id}   tags=['Categorias']
POST   /transacoes                  tags=['Transações']
GET    /transacoes                  tags=['Transações']
GET    /transacoes/exportar         tags=['Transações']
GET    /transacoes/{transacao_id}   tags=['Transações']
PUT    /transacoes/{transacao_id}   tags=['Transações']
DELETE /transacoes/{transacao_id}   tags=['Transações']
GET    /saldo                       tags=['Resumos e Exportação']
GET    /resumo                      tags=['Resumos e Exportação']
GET    /health                      tags=['Infraestrutura']
```

**Resultado:** 13 endpoints publicados, cobrindo todos os contratos da seção 4 da SDD, cada um
com uma única classificação.

> **Correção aplicada durante esta verificação:** o endpoint `/transacoes/exportar` aparecia
> duplicado no Swagger, por carregar uma tag própria além da tag do router. A tag redundante foi
> removida e a listagem acima é o resultado após a correção.

---

## 8. Interface web (RF08, RNF07)

Verificação feita com o container em execução e o navegador Microsoft Edge em modo headless
(`msedge --headless=new --screenshot`).

| Verificação | Resultado |
|---|---|
| `GET /` | `200 text/html; charset=utf-8` |
| `GET /style.css` | `200 text/css; charset=utf-8` |
| `GET /app.js` | `200 text/javascript; charset=utf-8` |
| Sintaxe do JavaScript (`node --check`) | sem erros |

**Aba Lançamentos.** Os cartões de resumo apresentam os mesmos valores devolvidos por
`GET /resumo`; a tabela lista as movimentações com data em formato brasileiro, etiqueta de
categoria, sinal `+`/`-` por tipo e ações de editar e excluir; o gráfico de despesas por categoria
traz nome, valor e percentual em cada barra. Paginação com "Anterior" e "Próxima" desabilitados
quando não há outra página.

**Aba Categorias.** Lista as categorias com ações de editar e excluir, e exibe o aviso sobre a
RN05.

**Tema escuro.** A página acompanha a preferência do sistema via `prefers-color-scheme`;
verificada com `--force-dark-mode`, sem perda de contraste.

Nenhuma sobreposição de rótulo ou estouro horizontal foi observada em nenhuma das telas.

---

## 9. Rastreabilidade — requisito × evidência

| Requisito | Descrição | Seção deste documento |
|---|---|---|
| RF01 | Cadastro de transações | 3 |
| RF02 | Gerenciamento de categorias personalizadas | 3, 4 (casos 5 a 7) |
| RF03 | Consulta de transações | 3 |
| RF04 | Exclusão de transações | 3 |
| RF05 | Filtros de busca | 3 |
| RF06 | Consulta de saldo | 3, 4 (caso 12) |
| RF07 | Resumo financeiro | 3, 4 (caso 11) |
| RF08 | Interface de usuário | 8 |
| RF09 | Exportação de relatório | 5 |
| RNF01 | Python e FastAPI | 1, 7 |
| RNF02 | SQLite, SQLAlchemy e persistência | 6 |
| RNF03 | Execução local em `localhost:8000` | 1, 2 |
| RNF04 | Conteinerização com Docker | 1 |
| RNF05 | Suíte de testes com Pytest | **pendente — issue #5** |
| RNF06 | Controle de versão e Pull Requests | PR #9, branch `feature/ambiente-docker-agente-ia` |
| RNF07 | Frontend sem framework | 8 |
| RNF08 | Documentação da API | 7 |
| RNF09 | Padronização de erros | 4 (casos 1 a 9) |
| RN01–RN08 | Regras de negócio | 4 |

---

## 10. Conclusão e pendência declarada

**Aprovado.** Todos os cenários executados devolveram o resultado previsto na especificação:
12 casos de borda, 8 cenários principais, exportação em CSV, persistência em volume e a interface
web. Nenhuma falha foi observada; a única correção necessária durante a verificação foi a tag
duplicada no Swagger, já aplicada e reconfirmada.

**Pendência declarada honestamente:** a validação registrada aqui é **manual**, feita por execução
dos endpoints e conferência das respostas contra os contratos da SDD. A suíte **automatizada com
Pytest exigida pelo RNF05 ainda não existe no repositório** — ela é a issue #5, sob
responsabilidade de outro integrante. O ambiente já está preparado para recebê-la, e os cenários
documentados nas seções 3 e 4 servem diretamente como roteiro dos casos de teste a implementar.

---

## Como reproduzir esta verificação

```bash
git clone https://github.com/LeoCeubs/sistema-controle-gastos-pessoais.git
cd sistema-controle-gastos-pessoais
docker compose down -v          # garante banco limpo
docker compose up --build -d
curl http://localhost:8000/health
curl http://localhost:8000/categorias
```

Em seguida, repetir as chamadas das seções 3 a 6 deste documento.
