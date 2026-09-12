# Página 3 — Ambiente e Agentes de IA

**Responsável:** Bhrenno Almeida Borges · **Issue:** #3 · **Pull Request:** #9

---

## 3.1 Descrição do Ambiente

O sistema é uma aplicação **local**: roda no computador do próprio usuário e nenhuma informação
financeira sai da máquina. Essa restrição é o que define toda a arquitetura descrita abaixo.

### FastAPI (RNF01)

A API REST foi construída em **Python com FastAPI**. A escolha resolve três exigências de uma vez:

- **Validação declarativa** — os contratos de entrada vivem em schemas Pydantic
  (`app/schemas.py`). Declarar `valor: float = Field(gt=0)` já implementa a RN02, e declarar
  `data: date` já implementa a RN03, inclusive rejeitando datas inexistentes como 30/02.
- **Documentação automática (RNF08)** — o Swagger/OpenAPI é gerado a partir do próprio código e
  fica em `http://localhost:8000/docs`, sempre sincronizado com a implementação.
- **Desempenho e simplicidade** — servidor ASGI (Uvicorn), sem camadas extras de configuração.

A API está organizada em um router por domínio, o que mantém as unidades isoladas e testáveis:

| Arquivo | Responsabilidade | Requisitos |
|---|---|---|
| `app/routers/categorias.py` | CRUD de categorias personalizadas | RF02, RN04, RN05 |
| `app/routers/transacoes.py` | CRUD, filtros, paginação e exportação CSV | RF01, RF03, RF04, RF05, RF09 |
| `app/routers/resumo.py` | Saldo e resumo financeiro | RF06, RF07, RN07, RN08 |
| `app/main.py` | Aplicação, arquivos estáticos e tratamento de erros | RF08, RNF09 |
| `app/models.py` / `app/database.py` | Modelagem e conexão | RNF02, RN06 |

**Padronização de erros (RNF09).** Dois *exception handlers* em `app/main.py` garantem que toda
falha saia no mesmo formato `{"erro": "mensagem"}` com status semântico. Isso foi necessário
porque o comportamento padrão do FastAPI é devolver `422` com `{"detail": [...]}`, formato que a
especificação não prevê — os handlers convertem para `400`.

### Banco SQLite (RNF02)

O armazenamento usa **SQLite acessado via SQLAlchemy**. SQLite é um banco em arquivo único, sem
servidor para instalar ou manter, o que é coerente com uma aplicação monousuário e offline.
O SQLAlchemy funciona como camada de mapeamento objeto-relacional, mantendo o código independente
do banco caso o projeto evolua.

Modelagem em duas entidades:

- **Categoria** — `id`, `nome` (único)
- **Transacao** — `id`, `valor`, `data`, `tipo` (receita/despesa), `categoria_id` (chave
  estrangeira), `descricao`

Categoria é uma **entidade própria**, e não um texto dentro da transação. Sem isso não haveria
como cumprir o RF02 (CRUD de categorias personalizadas), a RN04 (nome único) nem a RN05
(bloquear exclusão de categoria em uso, que é integridade referencial clássica).

Na primeira inicialização o sistema semeia as categorias padrão "Alimentação", "Salário" e
"Outros" (RN06), todas editáveis e removíveis.

### Conteinerização com Docker (RNF03, RNF04)

O ambiente inteiro é reproduzível por um comando. Ninguém precisa instalar Python, criar
ambiente virtual ou resolver conflito de versão de dependência — o problema clássico do
"na minha máquina funciona" deixa de existir.

- **`Dockerfile`** — imagem base `python:3.12-slim`. O `requirements.txt` é copiado antes do
  restante do código para aproveitar cache de camada: mudar o código não reinstala as dependências.
- **`docker-compose.yml`** — publica a porta `8000` (RNF03) e define o ponto mais importante da
  configuração: o **volume nomeado `dados`**, montado em `/app/data`, onde fica o arquivo
  `app.db`. Sem esse volume, o banco morreria junto com o container a cada `docker compose down`.
  Com ele, os dados sobrevivem à recriação do container — exigência explícita do RNF02.
- **`requirements.txt`** — versões fixadas (`fastapi==0.115.6`, `uvicorn==0.34.0`,
  `SQLAlchemy==2.0.36`, `pydantic==2.10.4`), para que todos rodem exatamente a mesma coisa.
- Em desenvolvimento, o compose ainda monta `./app` dentro do container com `--reload`: editar o
  código no host recarrega o servidor sem precisar reconstruir a imagem.

### Interface web (RF08, RNF07)

A interface é **HTML, CSS e JavaScript puro**, sem framework e sem etapa de build, servida pelo
próprio backend. Ela consome a mesma API documentada no Swagger e oferece painel de saldo e
resumo, cadastro e edição de movimentações, filtros com paginação, gerenciamento de categorias,
gráfico de despesas por categoria e exportação em CSV.

---

## 3.2 Agentes de IA Utilizados

**Ferramenta adotada:** **Claude Code** (Anthropic), modelo Claude Opus 5, executado pela extensão
nativa do Visual Studio Code em Windows 11.

**Por que essa ferramenta:** ela roda no editor com acesso ao sistema de arquivos do projeto, o que
significa que o agente lê a especificação, escreve os arquivos e **executa a validação** —
`docker compose`, `curl`, inspeção das respostas — na mesma sessão. Não existe o vaivém de copiar
código de um chat e colar na IDE, e cada afirmação de "funciona" vem acompanhada da saída real do
comando. Além disso, ela suporta arquivo de contexto versionado, que é exatamente o artefato
pedido no item "Contexto & Regras".

### Como a IA foi usada dentro do fluxo SDD

O agente foi configurado para seguir sempre a mesma sequência, registrada em `CLAUDE.md`:

| Etapa | O que acontece |
|---|---|
| **1. Spec** | Localizar na SDD o RF/RNF/RN que a tarefa atende. Não existindo requisito, o agente para e pergunta em vez de inventar. |
| **2. Contrato** | Conferir rota, método, corpo de entrada, corpo de saída e status HTTP exatos na seção 4 da SDD. |
| **3. Implementação** | Escrever o menor código que cumpre o contrato. |
| **4. Validação** | Exercitar o endpoint com `curl` ou pelo `/docs` e comparar a resposta real com o contrato, incluindo os casos de erro. |

A especificação, portanto, não é apenas documentação: ela é a **entrada** do processo de geração
de código, e o código só é aceito quando a saída observada bate com o contrato escrito.

### Onde a IA efetivamente ajudou

- **Leitura da especificação** — o PDF da SDD foi extraído e interpretado para levantar os 9 RFs,
  9 RNFs e 8 RNs antes de qualquer linha de código.
- **Geração da estrutura e dos endpoints** conforme os contratos da seção 4.
- **Detecção de divergências na própria especificação** — o exemplo de resposta do
  `POST /transacoes` mostra `categoria_id`, enquanto o do `GET /transacoes` mostra o objeto
  `categoria` aninhado. O agente apontou o conflito, e a decisão foi devolver os dois campos.
- **Prevenção de erros sutis** — a rota `/transacoes/exportar` precisa ser declarada antes de
  `/transacoes/{id}`, senão o parâmetro de caminho captura a palavra "exportar"; e o `422` padrão
  do FastAPI precisava ser convertido em `400` para respeitar o RNF09.
- **Execução da bateria de validação** e registro das evidências.

### Limites configurados para o agente

Deliberadamente, o agente **não** faz `git push`, não abre nem mescla Pull Requests, não instala
dependência nova sem aprovação, não troca a stack fixada pelos RNFs e não altera a SDD. Toda
divergência entre código e especificação vira uma pergunta ao grupo, não um improviso. O código
gerado só entra no repositório após revisão humana em Pull Request.

---

## 3.3 Prompts Globais

Os arquivos de instrução estão **versionados no repositório**, de modo que todo integrante herda
as mesmas regras e o agente responde de forma consistente em qualquer máquina.

| Arquivo | Papel |
|---|---|
| `CLAUDE.md` (raiz) | Contexto permanente, lido automaticamente no início de cada sessão |
| `docs/ia/agente.md` | Configuração da ferramenta e forma de uso pela equipe |
| `docs/ia/prompts.md` | Histórico dos prompts, no formato prompt → resultado → ajuste |

### Trecho do contexto global (`CLAUDE.md`)

> **Fluxo de trabalho — SDD.** Sempre nesta ordem, não pule etapas: 1. Spec — localizar na SDD o
> RF/RNF/RN que a tarefa atende; se não existir requisito, parar e perguntar. 2. Contrato —
> confirmar rota, método, corpo de entrada, corpo de saída e status HTTP exatos da seção 4.
> 3. Implementação — o menor código que cumpre o contrato. 4. Validação — exercitar o endpoint e
> comparar a resposta com o contrato, incluindo os casos de erro.
>
> **Stack — fixada pelos RNFs, não trocar:** Python + FastAPI (RNF01); SQLite + SQLAlchemy
> (RNF02); Docker e `http://localhost:8000` (RNF03, RNF04); Pytest (RNF05); HTML, CSS e
> JavaScript puro, sem framework (RNF07); Swagger em `/docs` (RNF08).
>
> **Convenções:** contratos da API em português, como estão na SDD; erro sempre em
> `{"erro": "mensagem"}` com status semântico; validação de entrada nos schemas Pydantic e
> regras que dependem do banco nos routers; rota literal antes de rota com parâmetro de caminho.
>
> **Limites do agente:** não faz push nem merge; não instala dependência sem aprovação; não altera
> a SDD — divergência vira pergunta.

### Exemplos de prompts usados

**Prompt bem formado — cita o requisito:**

> "Implemente o RF05 (filtros de busca) em `app/routers/transacoes.py`, respeitando a RN08:
> filtro sem resultado devolve 200 com lista vazia, não erro."

**Prompt de planejamento — abertura do trabalho:**

> "Leia a SDD e a nossa função e crie um plano para fazermos nossa parte completa. Estamos
> estritamente na parte 3."

**Prompt em que o agente recusou e explicou o porquê — refinamento por feedback:**

> "Utilize Streamlit para deixar a interface do front-end mais bonita."

O agente apontou que Streamlit é um framework de interface e contraria o RNF07 ("HTML, CSS e
JavaScript, sem a necessidade de frameworks complexos") e o RNF03 (a aplicação deve responder em
`http://localhost:8000`). Ofereceu três caminhos e o grupo optou por refinar o visual dentro da
stack da SDD. Este episódio está registrado em `docs/ia/prompts.md` e serve de evidência de
refinamento por feedback.

---

## 3.4 Comandos de Execução

### Pré-requisitos

Docker Desktop com Docker Compose v2. Nada além disso — não é necessário instalar Python.

### Subir a aplicação

```bash
docker compose up --build -d
```

| Endereço | O que é |
|---|---|
| `http://localhost:8000` | Interface web |
| `http://localhost:8000/docs` | Documentação interativa da API (Swagger) |
| `http://localhost:8000/health` | Verificação de que o serviço está no ar |

### Operação do dia a dia

```bash
docker compose logs -f api     # acompanhar os logs
docker compose ps              # ver o status do container
docker compose down            # parar (os dados permanecem no volume)
docker compose down -v         # parar e apagar o banco
docker compose up --build -d   # reconstruir após mudança nas dependências
```

### Execução alternativa, sem Docker

```bash
python -m venv .venv
.venv\Scripts\activate         # Windows
source .venv/bin/activate      # Linux / macOS

pip install -r requirements.txt
uvicorn app.main:app --reload
```

### Verificação rápida da API

```bash
curl http://localhost:8000/health
curl http://localhost:8000/categorias
curl -X POST http://localhost:8000/transacoes \
  -H "Content-Type: application/json" \
  -d '{"valor":150.50,"data":"2026-09-10","tipo":"despesa","categoria_id":1,"descricao":"Compra no mercado"}'
curl http://localhost:8000/saldo
```

### Harness de testes

O ambiente já está preparado para receber a suíte: basta acrescentar `pytest` e `httpx` ao
`requirements.txt` e os testes em `tests/`. Os comandos de execução serão:

```bash
docker compose run --rm api pytest -v              # dentro do container
docker compose run --rm api pytest -v --cov=app    # com relatório de cobertura
pytest -v                                          # localmente, na venv
```

> **Situação atual:** a suíte automatizada com Pytest é a **issue #5** e ainda não está no
> repositório. A validação já realizada foi feita por execução manual dos endpoints, com todas as
> saídas registradas em `docs/evidencias.md`.
