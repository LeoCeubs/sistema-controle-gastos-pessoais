# Configuração do Agente de IA

Documento do item 3 da entrega: qual ferramenta de geração de código foi adotada,
como está configurada e como o grupo deve usá-la.

## Ferramenta adotada

**Claude Code** (Anthropic), modelo **Claude Opus 5**, executado pela extensão nativa do
**Visual Studio Code** sobre Windows 11 / PowerShell.

Motivo da escolha:

- roda no terminal e no editor com acesso direto ao sistema de arquivos do projeto, então o
  agente lê a SDD, escreve os arquivos e **executa a validação** (`docker compose`, `curl`)
  na mesma sessão — sem copiar e colar código entre chat e IDE;
- suporta arquivo de contexto versionado (`CLAUDE.md`), que é justamente o artefato pedido
  em "Contexto & Regras";
- gratuito para o plano usado pela equipe e sem necessidade de configurar chave de API por membro.

## Instalação

```bash
npm install -g @anthropic-ai/claude-code   # CLI
claude                                     # primeira execução: autenticação no navegador
```

No VS Code: instalar a extensão **Claude Code** pela Marketplace e abrir a pasta do projeto.
O agente carrega o contexto sozinho ao iniciar a sessão.

## Arquivos de contexto versionados no repositório

| Arquivo | Papel |
|---|---|
| `CLAUDE.md` (raiz) | Regras permanentes: stack fixada pelos RNFs, regras de negócio, convenções de código, fluxo SDD e limites do agente. Lido automaticamente em toda sessão. |
| `docs/ia/agente.md` | Este documento: ferramenta, instalação, forma de uso. |
| `docs/ia/prompts.md` | Histórico dos prompts efetivamente usados, com resultado e ajuste. |
| `Especificação Técnica _ SDD.pdf` | Fonte da verdade dos requisitos. O agente consulta e **não** altera. |

Como `CLAUDE.md` está versionado, todo membro da equipe herda as mesmas regras — o agente
não responde de um jeito na máquina de um e de outro na máquina do colega.

Quem usar **Cursor** pode criar um `.cursorrules` com o conteúdo do `CLAUDE.md`;
quem usar **Codex CLI**, um `AGENTS.md` apontando para ele. O `CLAUDE.md` continua sendo o original.

## Como o grupo deve pedir mudanças (fluxo SDD)

Todo prompt precisa citar o requisito. O agente foi instruído a parar e perguntar quando a
tarefa não tem requisito correspondente na SDD.

```
Implemente o RF05 (filtros de busca) em app/routers/transacoes.py,
respeitando a RN08: filtro sem resultado devolve 200 com lista vazia, não erro.
```

Sequência esperada de cada tarefa:

1. **Spec** — identificar o RF/RNF/RN na SDD.
2. **Contrato** — conferir rota, corpo de entrada/saída e status HTTP na seção 4 da SDD.
3. **Implementação** — menor código que cumpre o contrato.
4. **Validação** — chamar o endpoint e comparar a resposta real com o contrato, inclusive erros.

O passo 4 não é opcional: as evidências de execução ficam em `docs/ia/prompts.md`.

## Limites configurados

- Não faz `git push`, não abre nem mescla Pull Request, não mexe em branch protegida —
  versionamento e code review são feitos pelas pessoas (RNF06).
- Não adiciona dependência nem troca tecnologia da stack sem aprovação do grupo.
- Não edita a SDD. Divergência entre código e especificação vira pergunta ao grupo.
- Código gerado só entra no repositório depois de revisão humana em Pull Request.

## Registro de uso

Cada sessão relevante entra em `docs/ia/prompts.md` com: prompt usado, o que o agente
produziu e o ajuste humano feito depois. É a evidência de "uso documentado" da entrega.
