# CLAUDE.md — Instruções do agente de IA

Arquivo de contexto lido automaticamente pelo Claude Code no início de cada sessão.
Vale para qualquer agente usado no projeto (Cursor, Codex CLI etc.) — leia antes de gerar código.

## O projeto

Sistema de Controle de Gastos Pessoais: API REST local + interface web para registrar
receitas e despesas, categorizá-las, filtrar, consultar saldo/resumo e exportar CSV.
Requisito central: **os dados nunca saem da máquina do usuário**.

A fonte da verdade é o documento `Especificação Técnica _ SDD.pdf` na raiz.
Todo requisito tem código: `RF01..RF09` (funcionais), `RNF01..RNF09` (não funcionais),
`RN01..RN08` (regras de negócio).

## Fluxo de trabalho — SDD (Spec-Driven Development)

Sempre nesta ordem. Não pule etapas.

1. **Spec** — localizar na SDD o RF/RNF/RN que a tarefa atende. Se não existir requisito, parar e perguntar.
2. **Contrato** — confirmar rota, método, corpo de entrada, corpo de saída e status HTTP exatos da seção 4 da SDD.
3. **Implementação** — o menor código que cumpre o contrato.
4. **Validação** — exercitar o endpoint (curl / `/docs`) e comparar a resposta com o contrato, incluindo os casos de erro.

Prompt bem formado cita o requisito. Ex.: *"Implemente o RF05 respeitando a RN08"*.

## Stack — fixada pelos RNFs, não trocar

| Camada | Tecnologia | Requisito |
|---|---|---|
| Linguagem / API | Python + FastAPI | RNF01 |
| Banco / ORM | SQLite + SQLAlchemy | RNF02 |
| Execução | Docker + docker compose, `http://localhost:8000` | RNF03, RNF04 |
| Testes | Pytest | RNF05 |
| Frontend | HTML + CSS + JavaScript puro, sem framework | RNF07 |
| Documentação | Swagger/OpenAPI automático em `/docs` | RNF08 |

Não adicionar dependência nova sem justificar contra a stdlib. O CSV do RF09 usa o módulo
`csv` da biblioteca padrão — não usar pandas.

## Regras de negócio (resumo — detalhe na SDD)

- **RN01** — `valor`, `data`, `tipo`, `categoria_id` obrigatórios; faltou algum → 400.
- **RN02** — `valor > 0` estrito. O sinal vem do campo `tipo`, nunca do valor.
- **RN03** — data em ISO 8601 `YYYY-MM-DD`; data inexistente (30/02) é rejeitada.
- **RN04** — nome de categoria único ignorando maiúsculas/minúsculas.
- **RN05** — não excluir categoria vinculada a transações → 400 `{"erro":"Categoria em uso."}`.
- **RN06** — na primeira inicialização, semear "Alimentação", "Salário", "Outros" (editáveis e removíveis).
- **RN07** — saldo pode ficar negativo. Nunca bloquear cadastro de despesa por causa do saldo.
- **RN08** — filtro sem resultado devolve 200 com `[]` e totais zerados, **nunca** erro.

## Convenções de código

- Contratos da API em **português** (`valor`, `data`, `tipo`, `categoria_id`, `descricao`, `saldo_atual`,
  `total_receitas`, `total_despesas`, `saldo_periodo`) — são os nomes da SDD, não traduzir.
- **Erro sempre em JSON `{"erro": "mensagem"}`** com status semântico 200/201/204/400/404 (RNF09).
  Os handlers em `app/main.py` convertem o 422 padrão do FastAPI em 400 nesse formato — não remover.
- Validação de entrada mora nos schemas Pydantic (`app/schemas.py`); regra que depende do banco
  (unicidade, integridade referencial) mora no router.
- Um router por domínio: `categorias.py`, `transacoes.py`, `resumo.py`.
- Rota literal antes de rota com path param (`/transacoes/exportar` antes de `/transacoes/{id}`).
- Docstring curta em cada endpoint citando o RF que ele atende.
- Comentário só onde a intenção não é óbvia — de preferência apontando o requisito.

## Limites do agente

- Não faz `git push`, não abre nem mescla Pull Request, não altera branch protegida.
- Não instala dependência nem muda a stack sem aprovação do grupo.
- Não altera a SDD: divergência entre código e spec vira pergunta, não improviso.
- Toda sessão relevante deve ser registrada em `docs/ia/prompts.md`.
