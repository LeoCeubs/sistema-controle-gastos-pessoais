# Sistema de Controle de Gastos Pessoais

Aplicação web e API local em Python para controle financeiro, permitindo cadastrar receitas, despesas e consultar saldos com persistência em SQLite.

---

## 🚀 Tecnologias Utilizadas
- **Linguagem:** Python 3.x
- **Framework Web/API:** FastAPI
- **Banco de Dados:** SQLite com SQLAlchemy ORM
- **Testes Automatizados:** Pytest
- **Containerização:** Docker e Docker Compose
- **Versionamento & Governança:** GitHub (Issues, Projects, PRs)

---

## 🛠️ Endpoints da API
- `POST /transacoes`: Cadastrar receita ou despesa
- `GET /transacoes`: Listar movimentações cadastradas
- `GET /transacoes?mes=X&categoria=Y`: Filtrar movimentações
- `GET /transacoes/{id}`: Consultar movimentação específica
- `DELETE /transacoes/{id}`: Excluir movimentação
- `GET /saldo`: Consultar saldo atual
- `GET /resumo`: Consultar resumo financeiro consolidado

---

## 📋 Como Executar o Projeto
*(Seção sob responsabilidade de Bhrenno - preencher com comandos Docker e ambiente virtual)*

---

## 🧪 Como Executar os Testes Automatizados
*(Seção sob responsabilidade de Alexandre - preencher com os comandos do Pytest)*

---

## 👥 Equipe e Responsabilidades
- **Alexandre:** Testes automatizados (Pytest), endpoints de saldo/resumo e relatórios/evidências.
- **Arthur:** Especificação técnica SDD, requisitos, regras de negócio e filtros.
- **Bhrenno:** Estrutura FastAPI, Docker/docker-compose, banco de dados e documentação da IA.
- **Léo:** Governança do repositório no GitHub, branches, projetos/issues e endpoints de transações.# sistema-controle-gastos-pessoais
