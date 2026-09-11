# Registro de Prompts

Histórico dos prompts usados com o agente de IA (Claude Code / Claude Opus 5), o que cada um
produziu e o ajuste humano feito depois. Evidência de "uso documentado" exigida no item 3 da entrega.

Formato de cada entrada: **Prompt → Resultado → Ajuste**.

---

## Sessão 1 — 10/09/2026 — Ambiente padronizado e agente de IA (item 3)

### Prompt 1 — leitura da especificação e planejamento

> "Leia a SDD e a nossa função e crie um plano para fazermos nossa parte completa. [escopo do
> professor colado] Estamos estritamente apenas na parte 3."

**Resultado:** o agente extraiu o texto do `Especificação Técnica _ SDD.pdf` (não havia
`pdftotext`/`pypdf` na máquina: escreveu um extrator de streams PDF + CMap `ToUnicode` em Python
puro), leu os 6 páginas de requisitos e produziu um plano cobrindo Dockerfile, docker-compose,
estrutura FastAPI, os contratos da seção 4 e o checklist de validação.

**Ajuste:** o agente avisou que implementar RF01–RF09 avança sobre o escopo dos colegas
(itens 2 e 4). O grupo decidiu, mesmo assim: **API completa, sem a suíte de testes**, sem
mexer em git, e instruções de agente em `CLAUDE.md` + `docs/ia/`.

### Prompt 2 — implementação

> Execução do plano aprovado.

**Resultado:** criados `Dockerfile`, `docker-compose.yml` (volume nomeado `dados`),
`requirements.txt`, `app/{main,database,models,schemas}.py`,
`app/routers/{categorias,transacoes,resumo}.py`, `static/index.html`, `CLAUDE.md` e `docs/ia/`.

**Ajustes feitos durante a implementação:**

1. **Erro padronizado (RNF09).** O FastAPI devolve `422` com `{"detail":[...]}` em erro de
   validação — formato que a SDD não prevê. Foi necessário um `RequestValidationError` handler
   convertendo para `400` + `{"erro":"..."}`, e outro para `HTTPException` trocando `detail` por `erro`.
2. **Contrato divergente na própria SDD.** A resposta do `POST /transacoes` mostra `categoria_id`,
   enquanto o `GET /transacoes` mostra o objeto `categoria` aninhado. A saída passou a incluir
   **os dois campos**, atendendo aos dois exemplos.
3. **Ordem de rotas.** `GET /transacoes/exportar` foi declarada **antes** de `GET /transacoes/{id}`,
   senão o path param captura a string "exportar" e o export quebra com 422/404.
4. **Persistência (RNF02).** `DATABASE_URL` aponta para `/app/data/app.db` e o compose mapeia o
   volume nomeado `dados` nesse caminho — sem isso o banco morre a cada `docker compose down`.

### Prompt 3 — validação

> Execução do checklist de verificação do plano.

**Resultado:** a suíte manual abaixo passou inteira, com o container em execução.

---

## Evidências de execução — 10/09/2026

Ambiente: Docker 29.1.2, Docker Compose v2.40.3, Windows 11.

```
$ docker compose up --build -d
 Network sistemadecontroledegastospessoais_default  Created
 Volume sistemadecontroledegastospessoais_dados     Created
 Container gastos-api                               Started

$ docker compose logs api
INFO:     Uvicorn running on http://0.0.0.0:8000 (Press CTRL+C to quit)
INFO:     Application startup complete.
```

### Casos de erro (RNF09 — status semântico + `{"erro": ...}`)

```
POST /categorias  {"nome":"ALIMENTAÇÃO"}                     -> HTTP 400 {"erro":"Categoria já cadastrada."}          (RN04)
POST /transacoes  {"valor":0,...}                            -> HTTP 400 {"erro":"valor: Input should be greater than 0"}  (RN02)
POST /transacoes  {"data":"2026-02-30",...}                  -> HTTP 400 {"erro":"data: Input should be a valid date or datetime, day value is outside expected range"}  (RN03)
POST /transacoes  sem o campo data                           -> HTTP 400 {"erro":"data: Field required"}              (RN01)
DELETE /categorias/1  (categoria com transação vinculada)    -> HTTP 400 {"erro":"Categoria em uso."}                 (RN05)
GET /transacoes/999                                          -> HTTP 404 {"erro":"Transação não encontrada."}
PUT /categorias/999                                          -> HTTP 404 {"erro":"Categoria não encontrada."}
```

### Casos principais

```
GET  /health         -> HTTP 200 {"status":"ok"}
GET  /categorias     -> HTTP 200 [{"id":1,"nome":"Alimentação"},{"id":2,"nome":"Salário"},{"id":3,"nome":"Outros"}]   (RN06 - seed)
POST /transacoes     -> HTTP 201 {"id":1,"valor":150.5,"data":"2026-09-10","tipo":"despesa","categoria_id":1,
                                  "categoria":{"id":1,"nome":"Alimentação"},"descricao":"Compra no mercado"}          (RF01)
POST /transacoes     -> HTTP 201 {"id":2,"valor":3000.0,"data":"2026-09-05","tipo":"receita","categoria_id":2,...}    (RF01)
GET  /transacoes?categoria=2   -> HTTP 200 [ ... apenas a receita de Salário ... ]                                    (RF05)
GET  /transacoes?mes=09&ano=2026 -> HTTP 200 [ 2 registros ]                                                          (RF05)
PUT  /transacoes/1   -> HTTP 200 {"id":1,"valor":160.0,"data":"2026-09-11", ... "(valor corrigido)"}                  (Ajuste 1 da SDD)
GET  /saldo          -> HTTP 200 {"saldo_atual":2849.5}                                                               (RF06)
GET  /resumo?mes=09&ano=2026 -> HTTP 200 {"total_receitas":3000.0,"total_despesas":150.5,"saldo_periodo":2849.5}      (RF07)
DELETE /transacoes/1 -> HTTP 204                                                                                      (RF04)
```

### Casos de borda

```
GET /transacoes?mes=1&ano=1999 -> HTTP 200 []                                                       (RN08 - sem erro)
GET /resumo?mes=1&ano=1999     -> HTTP 200 {"total_receitas":0.0,"total_despesas":0.0,"saldo_periodo":0.0}  (RN08)
POST /transacoes (despesa de 5000 com saldo insuficiente) -> HTTP 201; GET /saldo -> {"saldo_atual":-2160.0}  (RN07)
```

### Exportação CSV (RF09)

```
$ curl -D - "http://localhost:8000/transacoes/exportar?mes=09&ano=2026"
HTTP/1.1 200 OK
content-disposition: attachment; filename="relatorio_gastos.csv"
content-type: text/csv; charset=utf-8

id;data;tipo;categoria;valor;descricao
2;2026-09-05;receita;Salário;3000.00;Salario
1;2026-09-11;despesa;Alimentação;160.00;Compra no mercado (valor corrigido)
```

### Persistência em volume Docker (RNF02)

```
$ curl http://localhost:8000/saldo
{"saldo_atual":-2160.0}

$ docker compose down && docker compose up -d

$ curl http://localhost:8000/saldo
{"saldo_atual":-2160.0}          # dados sobreviveram à recriação do container
```

Depois da validação os registros de teste foram removidos; o banco ficou apenas com as três
categorias padrão da RN06.

---

## Sessão 2 — 10/09/2026 — Interface web (RF08)

### Prompt

> "Agora termine o front-end."

**Resultado:** criados `static/index.html`, `static/style.css` e `static/app.js` — HTML, CSS e
JavaScript puro, sem framework nem etapa de build (RNF07), servidos pelo próprio backend em
`http://localhost:8000` (RNF03). A interface cobre RF01 a RF09: painel de saldo e resumo,
formulário de cadastro/edição de movimentações, tabela com filtros de mês/ano/categoria,
paginação `limit`/`offset`, aba de gerenciamento de categorias e botão de exportar CSV.

**Ajustes feitos durante a implementação:**

1. **Aproveitar o navegador em vez de escrever código.** `input type="date"` já produz
   `YYYY-MM-DD` e recusa data inexistente (RN03); `input type="number" min="0.01"` cobre a RN02
   no cliente; `Intl.NumberFormat("pt-BR")` formata a moeda. Nenhuma biblioteca foi adicionada.
2. **Texto do usuário via `textContent`, nunca `innerHTML`.** Descrição e nome de categoria são
   inseridos como texto, o que evita injeção de HTML vindo dos próprios dados.
3. **Erro tratado em um ponto só.** O helper `api()` lê o `{"erro": "..."}` do RNF09 e lança
   `Error`; cada tela apenas exibe a mensagem no aviso do topo.
4. **Deep link por hash.** `trocarAba()` grava a aba no `location.hash`, então
   `/#categorias` abre direto na aba certa e a escolha sobrevive ao F5.

### Evidências de execução — interface renderizada

Verificação feita com o container em execução e o Microsoft Edge em modo headless
(`msedge --headless=new --screenshot`), com quatro movimentações de exemplo cadastradas:

```
$ curl -o /dev/null -w "%{http_code} %{content_type}" http://localhost:8000/
200 text/html; charset=utf-8
$ curl -o /dev/null -w "%{http_code} %{content_type}" http://localhost:8000/style.css
200 text/css; charset=utf-8
$ curl -o /dev/null -w "%{http_code} %{content_type}" http://localhost:8000/app.js
200 text/javascript; charset=utf-8

$ node --check static/app.js        # sintaxe do JavaScript
(sem erros)
```

Aba **Lançamentos** renderizada: cartões mostrando `R$ 3.200,00` de receitas, `R$ 282,70` de
despesas e `R$ 2.917,30` de saldo — coerentes com `GET /resumo?mes=9&ano=2026`. A tabela lista as
quatro movimentações com data em formato brasileiro, etiqueta de categoria, sinal `+`/`-` e ações
de editar/excluir. Paginação com "Anterior" e "Próxima" desabilitados quando não há outra página.

Aba **Categorias** renderizada: as três categorias padrão da RN06 (Alimentação, Salário, Outros)
com ações de editar e excluir, e o aviso sobre a RN05.

---

## Sessão 3 — 10/09/2026 — Refino visual da interface

### Prompt

> "Utilize Streamlit para deixar a interface do front-end mais bonita."

**Resultado — o agente recusou executar como pedido e explicou o porquê:** Streamlit é um
framework Python de interface, o que contraria o **RNF07** ("HTML, CSS e JavaScript, sem a
necessidade de frameworks complexos") e o **RNF03** (aplicação em `http://localhost:8000`;
o Streamlit sobe em outra porta). Foram oferecidas três saídas: Streamlit como painel extra
em paralelo, Streamlit substituindo a interface, ou refino visual dentro do HTML/CSS/JS.

**Decisão do grupo:** manter a stack da SDD e apenas refinar o visual existente.

**Ajuste aplicado:** `style.css` reescrito com tokens de cor em `:root`, tema escuro automático
por `prefers-color-scheme`, tipografia e espaçamento revisados, abas em pílula, cartões com
faixa lateral colorida e tabela mais limpa. Foi acrescentado um gráfico de **despesas por
categoria** em barras horizontais feitas com CSS puro — sem biblioteca de gráficos, mantendo o
RNF07.

Decisões do gráfico, seguindo boas práticas de visualização de dados:

- comparação de magnitude entre categorias pede **barra horizontal ordenada**, com **uma única
  cor** (escala sequencial), não uma cor por categoria;
- a cor usada (`#2a78d6` no claro, `#3987e5` no escuro) foi verificada por validador de paleta:
  passa em faixa de luminosidade, croma e contraste mínimo de 3:1 contra as duas superfícies;
- **rótulo direto** em cada barra (nome, valor e percentual) e `aria-label` por barra, de modo que
  a informação nunca depende só da cor — atende daltonismo e leitores de tela;
- acima de seis categorias, as menores são agrupadas em "Outras" em vez de virar uma sopa de barras.

### Evidências de execução

```
$ node --check static/app.js
(sem erros)

$ node scripts/validate_palette.js "#2a78d6" --mode light
[PASS] Lightness band / Chroma floor / Contrast vs surface   -> ALL CHECKS PASS

$ node scripts/validate_palette.js "#3987e5" --mode dark
[PASS] Lightness band / Chroma floor / Contrast vs surface   -> ALL CHECKS PASS
```

Páginas renderizadas e conferidas no Microsoft Edge headless
(`msedge --headless=new --screenshot`, com e sem `--force-dark-mode`): no tema claro e no escuro
os cartões mostram `R$ 3.200,00` de receitas, `R$ 282,70` de despesas e `R$ 2.917,30` de saldo,
o gráfico mostra Alimentação com `R$ 192,80` (68%) e Outros com `R$ 89,90` (32%), e a tabela
lista as quatro movimentações com sinal e cor por tipo. Nenhuma sobreposição de rótulo ou
estouro horizontal.

---

## Sessões futuras

Adicionar aqui cada uso relevante do agente, mantendo o formato **Prompt → Resultado → Ajuste**.
