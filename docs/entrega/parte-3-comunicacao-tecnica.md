# 3. Comunicação Técnica, Defesa de Projeto & README Final

Texto da seção 3 do relatório da Entrega 2. Substitui a versão preliminar que estava no relatório
da parte 1, corrigindo afirmações que não batiam com o código.

---

## 3.1 Documentação Completa (README.md)

O `README.md` na raiz do repositório é o ponto de entrada do projeto. Alguém que nunca viu o código
consegue, só com ele, entender o que o sistema faz, subir o ambiente e testar. Ele contém:

- **Visão geral e requisito central:** API REST local com interface web; nenhum dado financeiro sai
  da máquina do usuário.
- **Arquitetura da solução:** diagrama de componentes (navegador, container Docker com FastAPI,
  routers, schemas, ORM e banco SQLite em volume) e tabela com a responsabilidade de cada camada.
- **Diagrama do fluxo da aplicação:** diagrama de sequência do cadastro de uma despesa, da interface
  ao banco, incluindo os desvios de erro (400 por validação, 404 por categoria inexistente).
  Os diagramas são escritos em Mermaid, que o GitHub desenha direto no README, sem imagem para
  manter atualizada.
- **Instalação e execução em ambiente padronizado:** `docker compose up --build` como caminho
  principal; venv Python como alternativa; endereços da interface, do Swagger (`/docs`) e do
  `/health`; como parar o ambiente mantendo ou apagando os dados.
- **Testes automatizados:** comando para rodar a suíte Pytest dentro do container e o aviso sobre a
  dependência do banco inicializado.
- **Referência da API:** tabela de endpoints por domínio com o requisito que cada um atende, exemplo
  de `curl` e o formato padronizado de erro.
- **Estrutura de pastas, resumo dos ADRs e links** para evidências, registro de prompts e
  configuração do agente de IA.

> [INSERIR PRINT 9: README renderizado no GitHub, seção Arquitetura com o diagrama de componentes]
>
> Figura 9: Arquitetura da solução no README.md do repositório.

> [INSERIR PRINT 10: README renderizado no GitHub, diagrama de sequência e seção Como executar]
>
> Figura 10: Fluxo da aplicação e guia de execução no README.md.

## 3.2 Defesa das Decisões de Projeto (ADRs)

As decisões estão consolidadas em `docs/adr.md`, uma por seção, cada uma com contexto, decisão,
alternativas descartadas e trade-off aceito. Resumo:

| ADR | Decisão | Por quê | Trade-off aceito |
|---|---|---|---|
| 01 | Python + FastAPI | Validação declarativa com Pydantic e Swagger automático (RNF01, RNF08) | Formato de erro padrão precisou ser sobrescrito |
| 02 | SQLite + SQLAlchemy em volume Docker | Arquivo único, sem servidor, dados ficam na máquina (RNF02) | Escrita concorrente limitada; `lower()` só ASCII |
| 03 | Docker Compose | Mesmo ambiente para os quatro integrantes (RNF03, RNF04) | Exige Docker Desktop |
| 04 | HTML/CSS/JS puro servido pela API | RNF07; sem build e sem CORS | DOM e estado escritos à mão |
| 05 | Erro único `{"erro": ...}` | RNF09; um só tratamento no frontend | Só o primeiro erro de validação é devolvido |
| 06 | CSV pela stdlib | RF09 sem pandas | Formatação manual |
| 07 | Validação de campo no schema, regra de banco no router | Requisição inválida não chega ao banco | Duas camadas para conhecer |
| 08 | `main`/`develop`/`feature/*` com PR e aprovação obrigatória | Nada entra sem revisão de um par | Ciclo mais lento |
| 09 | Agente de IA governado por `CLAUDE.md` e fluxo SDD | Impede troca de stack e ações de governança pela IA | Contexto inicial e prompts mais longos |
| 10 | Pytest + `TestClient` | Testa o caminho HTTP completo | Suíte não isolada do banco da aplicação |

Duas correções em relação à versão preliminar desta seção:

- O ADR do FastAPI citava "alta performance assíncrona" como motivo. Os endpoints são síncronos, e
  o motivo real da escolha foi a validação e a documentação automáticas.
- Os ADRs 07 a 10 não existiam e foram acrescentados: validação em camadas, governança Git, uso
  governado de IA e estratégia de testes também são decisões de projeto com trade-off.

O documento termina com uma tabela de **dívidas registradas**, encontradas durante a revisão da
documentação e deixadas para decisão do grupo (isolamento dos testes, RN04 com acentos maiúsculos e
a `main` ainda no commit inicial).

## 3.3 Relato de Experiência

**Divisão do trabalho.** O grupo dividiu a entrega por frente: transações e endpoints iniciais,
ambiente padronizado e agente de IA, testes automatizados, e governança e relatório. Cada frente
virou uma issue no GitHub Projects e uma branch própria. A divisão permitiu trabalho paralelo, mas
também mostrou que frentes "independentes" se tocam o tempo todo: os testes dependem de como o
banco é criado, a interface depende do formato de erro, e o README depende de tudo.

**A especificação como contrato entre pessoas.** O maior ganho do SDD foi ter a SDD como árbitro.
Quando a própria especificação se contradisse (o `POST /transacoes` mostra `categoria_id` na
resposta e o `GET` mostra o objeto `categoria`), a divergência virou discussão registrada, e não uma
escolha silenciosa de quem estava codando. A saída passou a devolver os dois campos. O mesmo valeu
para o formato de erro: o padrão do FastAPI (`422` + `detail`) não é o da SDD (`400` + `erro`), e a
adaptação foi decidida a partir do RNF09, não do gosto de cada um.

**Governança na prática.** A proteção da `develop` funcionou: nenhum código entrou sem PR aprovado.
Mas ela não protege contra erro de processo. Dois exemplos do nosso histórico:

- A mesma branch `feature/transacoes-endpoints` gerou dois PRs (#7 e #8) com commits de mesmo
  conteúdo, mesclados um depois do outro.
- Dois commits de documentação foram feitos numa branch cujo PR (#9) já tinha sido mesclado e
  ficaram fora da `develop` até serem reaplicados numa branch nova.

Aprendizado: branch mesclada é branch encerrada; trabalho novo começa de uma branch nova a partir
da `develop` atualizada.

**IA como acelerador, não como autor.** O agente acelerou muito o trabalho repetitivo: estrutura do
projeto, Dockerfile, routers, interface e levantamento das evidências. Os acertos vieram quando
o contexto estava escrito (`CLAUDE.md` com stack, regras e limites). Os desvios vieram quando não
estava: ao pedir uma interface "melhor", a sugestão foi Streamlit, que violava dois requisitos. O
fluxo Spec → Contrato → Implementação → Validação foi o que transformou "a IA gerou" em "o grupo
verificou".

**Testes mostram o que a revisão não vê.** A suíte automatizada passou nas máquinas da equipe, mas
ao rodá-la num banco limpo, durante a revisão desta documentação, três dos quatro testes falharam:
o `TestClient` sem bloco `with` não executa a inicialização do banco, e os testes só passavam porque
o banco já existia de execuções anteriores. Na mesma revisão apareceu um caso de borda que nenhum
teste cobria: o `lower()` do SQLite não converte letras acentuadas, então `"ALIMENTAÇÃO"` é aceita
como categoria nova, contra a RN04. Lição: "100% de passagem" vale tanto quanto o ambiente em que
foi medido, e casos de borda de idioma (acentos, `ç`) precisam estar no plano de testes de um
sistema em português.

**Desafios.** Conciliar ritmos e horários de quatro pessoas; manter a documentação alinhada com um
código que mudava em várias branches ao mesmo tempo; e resistir à tentação de aceitar código
gerado por IA que "funcionava" sem conferir contra a SDD.

**O que faríamos diferente.** Escrever os testes de cada requisito junto com o endpoint, e não
depois; isolar o banco de testes desde o primeiro dia; fechar cada branch no merge; e fazer o PR
`develop` → `main` a cada entrega, para que a branch estável sempre represente o que foi entregue.
