# Registro Consolidado de Decisões de Arquitetura (ADRs)

Cada decisão traz o contexto que a motivou, o que foi decidido, as alternativas descartadas e o
trade-off que o grupo aceitou. Os códigos RF/RNF/RN referem-se à `Especificação Técnica _ SDD.pdf`.

Status de todas: **aceita**.

---

## ADR-01 — Python + FastAPI para a API

**Contexto.** A SDD fixa Python (RNF01), exige documentação automática da API (RNF08) e define
regras de entrada (RN01–RN03) que precisam ser validadas em todos os endpoints de escrita.

**Decisão.** FastAPI com Pydantic 2. Os contratos de entrada e saída viram classes em
`app/schemas.py`, e a documentação Swagger em `/docs` é gerada a partir delas.

**Alternativas descartadas.** Flask: exigiria bibliotecas avulsas para validação (marshmallow) e
para OpenAPI (flasgger), mais código e mais pontos de divergência entre doc e implementação.
Django: ORM, admin e templates próprios, muito além do que um app monousuário precisa.

**Trade-offs.** Ganha-se validação declarativa e documentação sempre sincronizada com o código.
Perde-se controle sobre o formato padrão de erro do FastAPI, que precisou ser sobrescrito (ADR-05).
Os endpoints foram escritos como funções síncronas (`def`): o volume de um usuário local não
justifica `async`, e o driver SQLite padrão é síncrono.

## ADR-02 — SQLite com SQLAlchemy, persistido em volume Docker

**Contexto.** RNF02 pede SQLite; o requisito central é que os dados financeiros nunca saiam da
máquina do usuário; os dados precisam sobreviver à recriação do container.

**Decisão.** Banco em um único arquivo, `/app/data/app.db`, montado no volume nomeado `dados`.
Acesso via SQLAlchemy 2. O caminho vem da variável `DATABASE_URL`.

**Alternativas descartadas.** PostgreSQL em container: segundo serviço, credenciais e
configuração sem ganho para um único usuário. JSON em arquivo: sem consultas por mês/ano/categoria
nem integridade referencial (RN05).

**Trade-offs.** Zero servidor para instalar e backup por cópia de arquivo. Em troca, SQLite
serializa escritas, o que limita uso concorrente (irrelevante aqui), e suas funções de texto são
limitadas: `lower()` só converte ASCII, o que afeta a comparação de nomes com acento (ver
"Dívidas registradas"). O ORM mantém aberta a troca de banco sem reescrever consultas.

## ADR-03 — Docker Compose como forma padrão de execução

**Contexto.** Quatro integrantes, sistemas operacionais e versões de Python diferentes. RNF03 e
RNF04 exigem execução em `http://localhost:8000` em ambiente padronizado.

**Decisão.** `Dockerfile` com `python:3.12-slim` e dependências com versão fixada em
`requirements.txt`; `docker compose up --build` como comando único. Em desenvolvimento, o compose
monta `./app` e `./static` no container e roda o uvicorn com `--reload`.

**Alternativas descartadas.** Apenas venv com instruções no README: cada máquina acabaria com uma
versão diferente de Python e de dependência.

**Trade-offs.** Ambiente idêntico e um comando para subir. Exige Docker Desktop, que pesa e precisa
estar ligado. A execução sem Docker continua documentada como alternativa.

## ADR-04 — Frontend em HTML, CSS e JavaScript puro, servido pelo backend

**Contexto.** RNF07 proíbe framework de frontend; RF08 pede interface web.

**Decisão.** Três arquivos em `static/`, montados como `StaticFiles` na raiz do próprio FastAPI.
A interface fala com a API via `fetch`, na mesma origem.

**Alternativas descartadas.** React/Vue: proibidos pelo RNF07 e exigiriam Node e etapa de build.
Streamlit: chegou a ser sugerido por um agente de IA durante o refinamento da interface e foi
recusado por violar RNF07 e RNF03 (roda em outra porta).

**Trade-offs.** Sem build, sem dependência de Node e sem CORS, já que tudo está em
`localhost:8000`. Em troca, manipulação de DOM, estado da tela e paginação são escritos à mão.

## ADR-05 — Formato único de erro `{"erro": "mensagem"}`

**Contexto.** RNF09 define erros em JSON `{"erro": ...}` com status semântico (400/404). O FastAPI
responde falha de validação com `422` e `{"detail": [...]}`, formato que a SDD não prevê.

**Decisão.** Dois exception handlers em `app/main.py`: `RequestValidationError` vira `400` com a
primeira mensagem de erro, e `HTTPException` tem `detail` renomeado para `erro`.

**Trade-offs.** O frontend tem um só caminho de tratamento de erro e o contrato bate com a SDD.
Perde-se a lista completa de erros quando vários campos falham juntos: só o primeiro é devolvido.

## ADR-06 — Exportação CSV com a biblioteca padrão

**Contexto.** RF09 pede o download de `relatorio_gastos.csv` com os filtros aplicados.

**Decisão.** Módulo `csv` da stdlib, com BOM UTF-8 para o Excel abrir a acentuação corretamente.

**Alternativa descartada.** pandas: dezenas de megabytes de dependência para escrever poucas linhas.

**Trade-offs.** Imagem menor e uma dependência a menos. Formatação de colunas feita manualmente.

## ADR-07 — Onde mora cada validação

**Contexto.** Há regras que dependem só do dado recebido (campo obrigatório, `valor > 0`, data ISO
válida) e regras que dependem do estado do banco (nome de categoria único, categoria em uso,
categoria existente).

**Decisão.** Validação de campo nos schemas Pydantic (RN01, RN02, RN03). Regra que precisa consultar
o banco no router do domínio (RN04, RN05, existência de `categoria_id`). O campo `tipo` é um `Enum`
(`receita`/`despesa`); o sinal do lançamento vem dele, nunca do valor.

**Trade-offs.** Requisição malformada é barrada antes de tocar o banco, e cada regra tem um único
lugar. Quem dá manutenção precisa conhecer as duas camadas.

## ADR-08 — Governança de código: Git flow com Pull Request obrigatório

**Contexto.** Quatro pessoas alterando o mesmo repositório, com entrega avaliada pela rastreabilidade
do trabalho em equipe.

**Decisão.** `main` como versão estável, `develop` como integração e uma branch `feature/*` (ou
`docs/*`, `fix/*`) por tarefa. A `develop` é protegida: sem push direto, merge só via PR com ao
menos uma aprovação. Commits seguem prefixos semânticos (`feat:`, `fix:`, `docs:`, `chore:`), e
cada PR referencia sua issue no GitHub Projects.

**Trade-offs.** Nada chega à integração sem revisão de um par, e cada mudança tem autor, issue e
discussão. Em troca, o ciclo é mais lento, e a proteção não impede erros de processo: commits feitos
numa branch depois de seu PR já mesclado ficaram de fora da `develop` até serem reaplicados.

## ADR-09 — Agente de IA governado por contexto versionado e fluxo SDD

**Contexto.** O grupo usou agentes de IA (principalmente Claude Code; Antigravity para comparação).
Sem regras, o agente tende a trocar a stack, inventar contrato ou executar ações de governança.

**Decisão.** `CLAUDE.md` na raiz, lido automaticamente a cada sessão, com a stack fixada, as regras
de negócio, as convenções e os limites do agente (não faz `git push`, não abre nem mescla PR, não
instala dependência, não altera a SDD). Todo trabalho segue Spec → Contrato → Implementação →
Validação, e cada sessão relevante é registrada em `docs/ia/prompts.md`.

**Trade-offs.** O agente passa a citar requisitos e a parar diante de divergência em vez de
improvisar, e o uso de IA fica auditável. Custa a escrita inicial do contexto e prompts mais longos.
A revisão humana continua obrigatória: o contexto reduz o desvio, não o elimina.

## ADR-10 — Testes automatizados com Pytest e `TestClient`

**Contexto.** RNF05 exige testes automatizados com Pytest cobrindo cenário normal e de borda.

**Decisão.** `tests/test_api.py` usa o `TestClient` do FastAPI contra a aplicação real, rodando
dentro do container (`pytest` e `httpx` adicionados ao `requirements.txt`).

**Trade-offs.** Testes curtos, que exercitam o caminho HTTP completo, handlers de erro incluídos.
Em troca, a suíte usa o mesmo banco da aplicação: grava dados nele e depende de as tabelas já
existirem. Como o `TestClient` é criado sem bloco `with`, o evento de inicialização (`init_db`) não
roda durante os testes; em banco recém-criado, três dos quatro testes falham com
`no such table: categorias`. Com a API já iniciada uma vez, os quatro passam.

---

## Dívidas registradas

Encontradas na revisão desta documentação (20/10/2026). Ficam registradas para decisão do grupo, sem
correção nesta branch.

| Item | Efeito | Correção sugerida |
|---|---|---|
| Testes sem isolamento de banco (ADR-10) | Suíte falha em banco novo e polui o banco real | `with TestClient(app) as client:` ou fixture com `DATABASE_URL` temporário |
| `lower()` do SQLite só trata ASCII (ADR-02) | `"ALIMENTAÇÃO"` é aceita como categoria diferente de `"Alimentação"`, violando RN04 | Comparar com `str.casefold()` em Python ou guardar coluna de nome normalizado |
| `main` ainda no commit inicial | Versão estável não reflete o projeto entregue | PR `develop` → `main` ao fechar a entrega |
