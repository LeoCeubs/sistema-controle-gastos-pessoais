/*
 * RF08 - lógica da interface. JavaScript puro, sem framework (RNF07).
 * Consome a API na mesma origem em que a página é servida (http://localhost:8000).
 */

const TAMANHO_PAGINA = 20;

const moeda = new Intl.NumberFormat("pt-BR", { style: "currency", currency: "BRL" });
const el = (id) => document.getElementById(id);

let categorias = [];
let pagina = 0;
let temProximaPagina = false;

/* ---------------- comunicação com a API ---------------- */

async function api(rota, opcoes = {}) {
  const resposta = await fetch(rota, {
    headers: { "Content-Type": "application/json" },
    ...opcoes,
  });

  if (resposta.status === 204) return null;

  let corpo = null;
  try {
    corpo = await resposta.json();
  } catch (e) {
    corpo = null;
  }

  // RNF09: a API sempre devolve {"erro": "..."} em caso de falha
  if (!resposta.ok) {
    throw new Error((corpo && corpo.erro) || "Não foi possível comunicar com a API.");
  }
  return corpo;
}

function avisar(mensagem, tipo) {
  const caixa = el("aviso");
  caixa.textContent = mensagem;
  caixa.classList.toggle("sucesso", tipo === "sucesso");
  caixa.hidden = false;
  clearTimeout(avisar.timer);
  avisar.timer = setTimeout(() => {
    caixa.hidden = true;
  }, 4000);
}

/* ---------------- helpers ---------------- */

function dataBR(iso) {
  const partes = iso.split("-");
  return partes[2] + "/" + partes[1] + "/" + partes[0];
}

function hojeISO() {
  const agora = new Date();
  const mes = String(agora.getMonth() + 1).padStart(2, "0");
  const dia = String(agora.getDate()).padStart(2, "0");
  return agora.getFullYear() + "-" + mes + "-" + dia;
}

// RF05 - filtros de mês, ano e categoria escolhidos pelo usuário
function filtrosAtuais() {
  const parametros = new URLSearchParams();
  const mes = el("filtro-mes").value;
  const ano = el("filtro-ano").value;
  const categoria = el("filtro-categoria").value;
  if (mes) parametros.set("mes", mes);
  if (ano) parametros.set("ano", ano);
  if (categoria) parametros.set("categoria", categoria);
  return parametros;
}

function celula(texto, classe) {
  const td = document.createElement("td");
  td.textContent = texto;
  if (classe) td.className = classe;
  return td;
}

function botaoAcao(texto, classe, aoClicar) {
  const botao = document.createElement("button");
  botao.type = "button";
  botao.className = "botao link " + classe;
  botao.textContent = texto;
  botao.addEventListener("click", aoClicar);
  return botao;
}

/* ---------------- categorias (RF02) ---------------- */

async function carregarCategorias() {
  categorias = await api("/categorias");

  const selecaoForm = el("categoria");
  const selecaoFiltro = el("filtro-categoria");
  const escolhidaForm = selecaoForm.value;
  const escolhidaFiltro = selecaoFiltro.value;

  selecaoForm.innerHTML = "";
  selecaoFiltro.innerHTML = "";

  const todas = document.createElement("option");
  todas.value = "";
  todas.textContent = "Todas";
  selecaoFiltro.appendChild(todas);

  categorias.forEach((categoria) => {
    const opcao = document.createElement("option");
    opcao.value = categoria.id;
    opcao.textContent = categoria.nome;
    selecaoForm.appendChild(opcao);
    selecaoFiltro.appendChild(opcao.cloneNode(true));
  });

  selecaoForm.value = escolhidaForm || (categorias[0] && categorias[0].id) || "";
  selecaoFiltro.value = escolhidaFiltro;

  desenharCategorias();
}

function desenharCategorias() {
  const corpo = el("lista-categorias");
  corpo.innerHTML = "";

  categorias.forEach((categoria) => {
    const linha = document.createElement("tr");
    linha.appendChild(celula(categoria.id));
    linha.appendChild(celula(categoria.nome));

    const acoes = document.createElement("td");
    acoes.className = "direita";
    acoes.appendChild(botaoAcao("Editar", "", () => editarCategoria(categoria)));
    acoes.appendChild(botaoAcao("Excluir", "perigo", () => excluirCategoria(categoria)));
    linha.appendChild(acoes);

    corpo.appendChild(linha);
  });
}

function editarCategoria(categoria) {
  el("categoria-id").value = categoria.id;
  el("nome-categoria").value = categoria.nome;
  el("titulo-form-categoria").textContent = "Editar categoria";
  el("botao-salvar-categoria").textContent = "Salvar alterações";
  el("botao-cancelar-categoria").hidden = false;
  el("nome-categoria").focus();
}

function limparFormularioCategoria() {
  el("categoria-id").value = "";
  el("form-categoria").reset();
  el("titulo-form-categoria").textContent = "Nova categoria";
  el("botao-salvar-categoria").textContent = "Cadastrar";
  el("botao-cancelar-categoria").hidden = true;
}

async function excluirCategoria(categoria) {
  if (!confirm("Excluir a categoria " + categoria.nome + "?")) return;
  try {
    // RN05: a API bloqueia a exclusão se houver transação vinculada
    await api("/categorias/" + categoria.id, { method: "DELETE" });
    avisar("Categoria excluída.", "sucesso");
    await carregarCategorias();
    await atualizarLancamentos();
  } catch (erro) {
    avisar(erro.message);
  }
}

/* ---------------- transações (RF01, RF03, RF04) ---------------- */

async function carregarTransacoes() {
  const parametros = filtrosAtuais();
  parametros.set("limit", TAMANHO_PAGINA);
  parametros.set("offset", pagina * TAMANHO_PAGINA);

  const transacoes = await api("/transacoes?" + parametros.toString());
  temProximaPagina = transacoes.length === TAMANHO_PAGINA;

  const corpo = el("lista-transacoes");
  corpo.innerHTML = "";

  transacoes.forEach((transacao) => {
    const linha = document.createElement("tr");
    linha.appendChild(celula(dataBR(transacao.data)));

    const categoria = document.createElement("td");
    const etiqueta = document.createElement("span");
    etiqueta.className = "etiqueta";
    etiqueta.textContent = transacao.categoria.nome;
    categoria.appendChild(etiqueta);
    linha.appendChild(categoria);

    linha.appendChild(celula(transacao.descricao || "-", "descricao"));

    const sinal = transacao.tipo === "despesa" ? "- " : "+ ";
    const valor = celula(sinal + moeda.format(transacao.valor), "direita");
    valor.classList.add(transacao.tipo);
    linha.appendChild(valor);

    const acoes = document.createElement("td");
    acoes.className = "direita";
    acoes.appendChild(botaoAcao("Editar", "", () => editarTransacao(transacao)));
    acoes.appendChild(botaoAcao("Excluir", "perigo", () => excluirTransacao(transacao)));
    linha.appendChild(acoes);

    corpo.appendChild(linha);
  });

  // RN08: lista vazia é resultado válido, não erro
  el("vazio-transacoes").hidden = transacoes.length > 0;
  atualizarPaginacao();
}

function atualizarPaginacao() {
  el("pagina-info").textContent = "Página " + (pagina + 1);
  el("pagina-anterior").disabled = pagina === 0;
  el("pagina-proxima").disabled = !temProximaPagina;
}

function editarTransacao(transacao) {
  el("transacao-id").value = transacao.id;
  el("tipo").value = transacao.tipo;
  el("valor").value = transacao.valor;
  el("data").value = transacao.data;
  el("categoria").value = transacao.categoria_id;
  el("descricao").value = transacao.descricao || "";
  el("titulo-form").textContent = "Editar movimentação #" + transacao.id;
  el("botao-salvar").textContent = "Salvar alterações";
  el("botao-cancelar").hidden = false;
  trocarAba("lancamentos");
  el("valor").focus();
}

function limparFormularioTransacao() {
  el("transacao-id").value = "";
  el("form-transacao").reset();
  el("data").value = hojeISO();
  el("titulo-form").textContent = "Nova movimentação";
  el("botao-salvar").textContent = "Cadastrar";
  el("botao-cancelar").hidden = true;
}

async function excluirTransacao(transacao) {
  if (!confirm("Excluir a movimentação #" + transacao.id + "?")) return;
  try {
    await api("/transacoes/" + transacao.id, { method: "DELETE" });
    avisar("Movimentação excluída.", "sucesso");
    await atualizarLancamentos();
  } catch (erro) {
    avisar(erro.message);
  }
}

/* ---------------- gráfico de despesas por categoria ---------------- */

const MAX_BARRAS = 6;

function rotuloPeriodo() {
  const mes = el("filtro-mes");
  const ano = el("filtro-ano").value;
  const nomeMes = mes.value ? mes.options[mes.selectedIndex].textContent : "";
  if (nomeMes && ano) return nomeMes + " de " + ano;
  if (nomeMes) return nomeMes;
  if (ano) return ano;
  return "todo o período";
}

async function carregarGrafico() {
  const parametros = filtrosAtuais();
  parametros.set("limit", 500);
  const transacoes = await api("/transacoes?" + parametros.toString());

  // soma as despesas por categoria; receitas não entram neste recorte
  const somas = new Map();
  transacoes.forEach((transacao) => {
    if (transacao.tipo !== "despesa") return;
    const nome = transacao.categoria.nome;
    somas.set(nome, (somas.get(nome) || 0) + transacao.valor);
  });

  let linhas = Array.from(somas, ([nome, total]) => ({ nome, total })).sort(
    (a, b) => b.total - a.total
  );

  // mais de 6 categorias vira "Outras" em vez de virar sopa de barras
  if (linhas.length > MAX_BARRAS) {
    const resto = linhas.slice(MAX_BARRAS - 1);
    linhas = linhas.slice(0, MAX_BARRAS - 1);
    linhas.push({
      nome: "Outras (" + resto.length + ")",
      total: resto.reduce((soma, item) => soma + item.total, 0),
    });
  }

  el("grafico-periodo").textContent = rotuloPeriodo();

  const area = el("grafico");
  area.innerHTML = "";
  el("grafico-vazio").hidden = linhas.length > 0;
  if (linhas.length === 0) return;

  const maior = linhas[0].total;
  const total = linhas.reduce((soma, item) => soma + item.total, 0);

  linhas.forEach((linha) => {
    const parte = Math.round((linha.total / total) * 100);

    const bloco = document.createElement("div");
    bloco.className = "barra-linha";
    bloco.title = linha.nome + ": " + moeda.format(linha.total) + " (" + parte + "%)";

    const nome = document.createElement("span");
    nome.className = "barra-nome";
    nome.textContent = linha.nome;

    const trilha = document.createElement("div");
    trilha.className = "barra-trilha";
    trilha.setAttribute("role", "img");
    trilha.setAttribute(
      "aria-label",
      linha.nome + ": " + moeda.format(linha.total) + ", " + parte + " por cento das despesas"
    );

    const preenchida = document.createElement("div");
    preenchida.className = "barra-preenchida";
    preenchida.style.width = Math.max((linha.total / maior) * 100, 2) + "%";
    trilha.appendChild(preenchida);

    // rótulo direto: o valor não depende de legenda nem de hover
    const valor = document.createElement("span");
    valor.className = "barra-valor";
    valor.textContent = moeda.format(linha.total);
    const percentual = document.createElement("span");
    percentual.className = "barra-parte";
    percentual.textContent = parte + "%";
    valor.appendChild(percentual);

    bloco.append(nome, trilha, valor);
    area.appendChild(bloco);
  });
}

/* ---------------- saldo e resumo (RF06, RF07) ---------------- */

async function carregarResumo() {
  const parametros = new URLSearchParams();
  const mes = el("filtro-mes").value;
  const ano = el("filtro-ano").value;
  if (mes) parametros.set("mes", mes);
  if (ano) parametros.set("ano", ano);

  const consulta = parametros.toString();
  const resumo = await api("/resumo" + (consulta ? "?" + consulta : ""));
  const saldo = await api("/saldo");

  el("total-receitas").textContent = moeda.format(resumo.total_receitas);
  el("total-despesas").textContent = moeda.format(resumo.total_despesas);

  const periodo = el("saldo-periodo");
  periodo.textContent = moeda.format(resumo.saldo_periodo);
  periodo.classList.toggle("negativo", resumo.saldo_periodo < 0);

  // RN07: saldo negativo é permitido; a interface apenas destaca
  const atual = el("saldo-atual");
  atual.textContent = moeda.format(saldo.saldo_atual);
  atual.classList.toggle("negativo", saldo.saldo_atual < 0);
}

async function atualizarLancamentos() {
  try {
    await carregarTransacoes();
    await carregarResumo();
    await carregarGrafico();
  } catch (erro) {
    avisar(erro.message);
  }
}

/* ---------------- abas ---------------- */

function trocarAba(nome) {
  document.querySelectorAll(".aba").forEach((aba) => {
    aba.classList.toggle("ativa", aba.dataset.aba === nome);
  });
  el("painel-lancamentos").hidden = nome !== "lancamentos";
  el("painel-categorias").hidden = nome !== "categorias";
  // o hash permite abrir direto em /#categorias e sobrevive ao F5
  if (location.hash !== "#" + nome) location.hash = nome;
}

/* ---------------- eventos ---------------- */

document.querySelectorAll(".aba").forEach((aba) => {
  aba.addEventListener("click", () => trocarAba(aba.dataset.aba));
});

// RF01 - cadastro e edição de movimentações
el("form-transacao").addEventListener("submit", async (evento) => {
  evento.preventDefault();

  const corpo = {
    valor: Number(el("valor").value),
    data: el("data").value,
    tipo: el("tipo").value,
    categoria_id: Number(el("categoria").value),
    descricao: el("descricao").value.trim() || null,
  };

  const id = el("transacao-id").value;
  try {
    await api(id ? "/transacoes/" + id : "/transacoes", {
      method: id ? "PUT" : "POST",
      body: JSON.stringify(corpo),
    });
    avisar(id ? "Movimentação atualizada." : "Movimentação cadastrada.", "sucesso");
    limparFormularioTransacao();
    await atualizarLancamentos();
  } catch (erro) {
    avisar(erro.message);
  }
});

el("botao-cancelar").addEventListener("click", limparFormularioTransacao);

// RF02 - cadastro e edição de categorias
el("form-categoria").addEventListener("submit", async (evento) => {
  evento.preventDefault();

  const id = el("categoria-id").value;
  const corpo = { nome: el("nome-categoria").value.trim() };

  try {
    await api(id ? "/categorias/" + id : "/categorias", {
      method: id ? "PUT" : "POST",
      body: JSON.stringify(corpo),
    });
    avisar(id ? "Categoria atualizada." : "Categoria cadastrada.", "sucesso");
    limparFormularioCategoria();
    await carregarCategorias();
    await atualizarLancamentos();
  } catch (erro) {
    avisar(erro.message);
  }
});

el("botao-cancelar-categoria").addEventListener("click", limparFormularioCategoria);

// RF05 - aplicar e limpar filtros
el("form-filtros").addEventListener("submit", (evento) => {
  evento.preventDefault();
  pagina = 0;
  atualizarLancamentos();
});

el("botao-limpar").addEventListener("click", () => {
  el("form-filtros").reset();
  pagina = 0;
  atualizarLancamentos();
});

// RF09 - exportação em CSV (download direto pelo navegador)
el("botao-exportar").addEventListener("click", () => {
  const parametros = filtrosAtuais().toString();
  window.location.href = "/transacoes/exportar" + (parametros ? "?" + parametros : "");
});

// Ajuste 2 da SDD - paginação limit/offset
el("pagina-anterior").addEventListener("click", () => {
  if (pagina === 0) return;
  pagina -= 1;
  atualizarLancamentos();
});

el("pagina-proxima").addEventListener("click", () => {
  if (!temProximaPagina) return;
  pagina += 1;
  atualizarLancamentos();
});

/* ---------------- inicialização ---------------- */

(async function iniciar() {
  el("data").value = hojeISO();
  if (location.hash === "#categorias") trocarAba("categorias");
  try {
    await carregarCategorias();
  } catch (erro) {
    avisar(erro.message);
  }
  await atualizarLancamentos();
})();
