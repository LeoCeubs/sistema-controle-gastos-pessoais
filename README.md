# Sistema de Controle de Gastos Pessoais

API REST local com interface web para registrar receitas e despesas, organizá-las em categorias
personalizadas, filtrar por período, consultar saldo e resumo financeiro e exportar relatório em CSV.

O sistema roda inteiramente na máquina do usuário e guarda tudo em um banco SQLite local:
**nenhuma informação financeira sai do computador**. Projeto acadêmico desenvolvido segundo o
documento `Especificação Técnica _ SDD.pdf` (Spec-Driven Development).

## Stack

Python 3.12 · FastAPI · SQLAlchemy 2 · SQLite · Docker / Docker Compose · HTML, CSS e JavaScript puro

## Pré-requisitos

- [Docker Desktop](https://www.docker.com/products/docker-desktop/) com Docker Compose v2
- (alternativa sem Docker) Python 3.11 ou superior

## Como executar

### Com Docker (recomendado)

```bash
docker compose up --build
```

Pronto. A aplicação sobe em **http://localhost:8000**:

| Endereço | O que é |
|---|---|
| http://localhost:8000 | Interface web |
| http://localhost:8000/docs | Documentação interativa da API (Swagger) |
| http://localhost:8000/health | Status do serviço |

Parar: `docker compose down` — os dados **permanecem**, guardados no volume `dados`.
Para apagar o banco junto: `docker compose down -v`.

### Sem Docker

```bash
python -m venv .venv
.venv\Scripts\activate        # Windows
source .venv/bin/activate     # Linux / macOS

pip install -r requirements.txt
uvicorn app.main:app --reload
```

O banco é criado em `./data/app.db` na primeira execução, junto com as categorias padrão.

## Interface web

Abrindo `http://localhost:8000` o usuário tem, sem instalar nada além do Docker:

- **Painel de resumo** — receitas, despesas e saldo do período filtrado, mais o saldo total
  acumulado. Saldo negativo aparece em vermelho, mas não bloqueia nada (RN07).
- **Gráfico de despesas por categoria** — barras horizontais ordenadas por valor, respeitando o
  filtro ativo. Acima de seis categorias as menores viram "Outras". Cada barra traz nome, valor e
  percentual, então a leitura não depende da cor.
- **Tema claro e escuro** — a página acompanha automaticamente a preferência do sistema
  (`prefers-color-scheme`), sem botão nem configuração.
- **Aba Lançamentos** — formulário de cadastro/edição de receitas e despesas, tabela das
  movimentações, filtros por mês, ano e categoria, paginação e botão de exportar CSV.
- **Aba Categorias** — criar, renomear e excluir categorias personalizadas. A tentativa de
  excluir categoria em uso mostra a mensagem devolvida pela API (RN05).
- **Mensagens de erro** — qualquer falha da API (`{"erro": "..."}`) aparece em um aviso no topo
  da página, sem quebrar a navegação.

Atalho: `http://localhost:8000/#categorias` abre direto na aba de categorias.

## Endpoints

### Categorias

| Método | Rota | Descrição | Requisito |
|---|---|---|---|
| POST | `/categorias` | Cria categoria personalizada | RF02 |
| GET | `/categorias` | Lista as categorias | RF02 |
| PUT | `/categorias/{id}` | Atualiza o nome | RF02 |
| DELETE | `/categorias/{id}` | Remove (bloqueado se estiver em uso) | RF02, RN05 |

### Transações

| Método | Rota | Descrição | Requisito |
|---|---|---|---|
| POST | `/transacoes` | Cadastra receita ou despesa | RF01 |
| GET | `/transacoes` | Lista com filtros `mes`, `ano`, `categoria`, `limit`, `offset` | RF03, RF05 |
| GET | `/transacoes/{id}` | Consulta uma movimentação | RF03 |
| PUT | `/transacoes/{id}` | Atualiza uma movimentação | RF03 |
| DELETE | `/transacoes/{id}` | Exclui uma movimentação | RF04 |
| GET | `/transacoes/exportar` | Baixa `relatorio_gastos.csv` | RF09 |

### Resumos

| Método | Rota | Descrição | Requisito |
|---|---|---|---|
| GET | `/saldo` | Saldo atual (receitas − despesas) | RF06 |
| GET | `/resumo` | Totais do período (`mes`, `ano`) | RF07 |

Exemplo:

```bash
curl -X POST http://localhost:8000/transacoes \
  -H "Content-Type: application/json" \
  -d '{"valor":150.50,"data":"2026-09-10","tipo":"despesa","categoria_id":1,"descricao":"Compra no mercado"}'
```

Erros seguem sempre o mesmo formato, com status HTTP semântico:

```json
{ "erro": "Categoria em uso." }
```

## Estrutura do projeto

```
.
├── app/
│   ├── main.py              # aplicação FastAPI, handlers de erro, arquivos estáticos
│   ├── database.py          # conexão SQLite, sessão, criação de tabelas e seed
│   ├── models.py            # tabelas Categoria e Transacao (SQLAlchemy)
│   ├── schemas.py           # contratos de entrada/saída e validações (Pydantic)
│   └── routers/
│       ├── categorias.py    # RF02
│       ├── transacoes.py    # RF01, RF03, RF04, RF05, RF09
│       └── resumo.py        # RF06, RF07
├── static/                  # interface web (RF08)
│   ├── index.html           # estrutura da página
│   ├── style.css            # estilos
│   └── app.js               # consumo da API, filtros, paginação, exportação
├── docs/ia/                 # configuração do agente de IA e registro de prompts
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
└── CLAUDE.md                # regras de contexto para os agentes de IA
```

## Registro de decisões arquiteturais (ADRs)

**ADR-01 — Python + FastAPI para a API.** Validação de entrada declarativa via Pydantic (cobre
as regras RN01–RN03 sem código extra) e documentação Swagger gerada automaticamente, o que já
atende ao RNF08 sem esforço adicional. *Alternativa descartada:* Flask, que exigiria bibliotecas
avulsas para validação e documentação.

**ADR-02 — SQLite com SQLAlchemy, persistido em volume Docker.** SQLite é um único arquivo, sem
servidor de banco para instalar — coerente com o requisito de uso 100% local (RNF03). O arquivo
fica em `/app/data/app.db`, mapeado no volume nomeado `dados`, de modo que recriar o container não
apaga os dados (RNF02). O SQLAlchemy mantém a porta aberta para trocar de banco depois sem reescrever
as consultas. *Alternativa descartada:* PostgreSQL em container, que traria dependência de serviço
e configuração desnecessárias para um app monousuário.

**ADR-03 — Docker Compose como forma padrão de execução.** Elimina o "na minha máquina funciona":
qualquer integrante roda um comando único e obtém a mesma versão de Python e das dependências
(RNF04). O compose ainda monta `./app` dentro do container com `--reload`, então editar o código no
host recarrega o servidor sem rebuild.

**ADR-04 — Frontend em HTML, CSS e JavaScript puro, servido pelo próprio backend.** Sem build,
sem Node, sem framework (RNF07). Os arquivos estáticos saem do mesmo servidor da API, o que evita
CORS e mantém tudo em `http://localhost:8000`.

**ADR-05 — Formato único de erro `{"erro": "mensagem"}`.** O padrão do FastAPI para falha de
validação é `422` com `{"detail":[...]}`, formato que a SDD não prevê. Foram registrados dois
exception handlers em `app/main.py` que convertem qualquer erro para `{"erro": "..."}` com status
semântico (400 para dado inválido, 404 para não encontrado), cumprindo o RNF09 e dando ao frontend
um só caminho de tratamento.

**ADR-06 — CSV pela biblioteca padrão.** O RF09 é atendido com o módulo `csv` e um BOM UTF-8 para
o Excel abrir a acentuação corretamente. *Alternativa descartada:* pandas, dezenas de megabytes de
dependência para escrever poucas linhas de texto.

## Evidências de execução

Registro completo dos testes manuais dos endpoints, casos de borda e do teste de persistência
do volume: [`docs/ia/prompts.md`](docs/ia/prompts.md).

A suíte automatizada de testes (Pytest) e o relatório de execução correspondente fazem parte do
item 4 da entrega e serão adicionados pelo membro responsável.

## Uso de IA no desenvolvimento

O projeto usa **Claude Code** como agente de geração/auxílio de código, seguindo o fluxo SDD.
As regras permanentes do agente estão em [`CLAUDE.md`](CLAUDE.md); a configuração da ferramenta,
em [`docs/ia/agente.md`](docs/ia/agente.md); o histórico de prompts, em
[`docs/ia/prompts.md`](docs/ia/prompts.md).
