// Aplicação Frontend — DataMind AI

const formatarMoeda = (valor) => {
  return new Intl.NumberFormat('pt-BR', { style: 'currency', currency: 'BRL' }).format(valor || 0);
};

const formatarNumero = (valor) => {
  return new Intl.NumberFormat('pt-BR').format(valor || 0);
};

// ==========================================
// NAVEGAÇÃO ENTRE TELAS
// ==========================================
function navegarPara(tela) {
  const telas = ['dashboard', 'chat', 'audit'];
  telas.forEach(t => {
    const el = document.getElementById(`view-${t}`);
    const navBtn = document.getElementById(`nav-${t}`);
    if (t === tela) {
      el.classList.remove('hidden');
      navBtn.className = "nav-item w-full flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition text-white bg-indigo-600/20 text-indigo-400 border border-indigo-500/30";
    } else {
      el.classList.add('hidden');
      navBtn.className = "nav-item w-full flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition text-slate-400 hover:text-white hover:bg-slate-800";
    }
  });

  const titleEl = document.getElementById('page-title');
  const subEl = document.getElementById('page-subtitle');

  localStorage.setItem('datamind_active_view', tela);

  if (tela === 'dashboard') {
    titleEl.innerText = "Dashboard Executivo";
    subEl.innerText = "Acompanhe métricas em tempo real e converse com os dados.";
    carregarDashboard();
  } else if (tela === 'chat') {
    titleEl.innerText = "Analista de IA Corporativo";
    subEl.innerText = "Faça perguntas em linguagem natural diretamente para a base de dados.";
    inicializarAreaChat();
  } else if (tela === 'audit') {
    titleEl.innerText = "Auditoria & Logs de Segurança";
    subEl.innerText = "Rastreabilidade e governança de todas as consultas geradas pela IA.";
    carregarAuditoria();
  }

  lucide.createIcons();
}

// ==========================================
// TELA 1: DASHBOARD
// ==========================================
async function carregarDashboard() {
  try {
    // 1. Carrega KPIs
    const resKpis = await fetch('/api/kpis');
    if (resKpis.ok) {
      const kpis = await resKpis.json();
      document.getElementById('kpi-faturamento').innerText = formatarMoeda(kpis.faturamento_total);
      document.getElementById('kpi-vendas').innerText = formatarNumero(kpis.vendas_concluidas);
      document.getElementById('kpi-ticket').innerText = formatarMoeda(kpis.ticket_medio);
      document.getElementById('kpi-inadimplencia').innerText = formatarMoeda(kpis.inadimplencia_total);
      document.getElementById('kpi-clientes-inadimplentes').innerText = `${kpis.clientes_inadimplentes} clientes em atraso`;
    }

    // 2. Gráfico Mensal
    const resMensal = await fetch('/api/dashboard/vendas-mensais');
    if (resMensal.ok) {
      const dadosMensais = await resMensal.json();
      const meses = dadosMensais.map(d => d.mes);
      const faturamentos = dadosMensais.map(d => d.faturamento);

      const traceLinha = {
        x: meses,
        y: faturamentos,
        type: 'scatter',
        mode: 'lines+markers',
        line: { color: '#4f46e5', width: 3, shape: 'spline' },
        marker: { size: 6, color: '#4f46e5' },
        name: 'Faturamento'
      };

      const layoutLinha = {
        margin: { l: 60, r: 20, t: 20, b: 40 },
        paper_bgcolor: 'rgba(0,0,0,0)',
        plot_bgcolor: 'rgba(0,0,0,0)',
        xaxis: { gridcolor: '#f1f5f9' },
        yaxis: { gridcolor: '#f1f5f9', tickprefix: 'R$ ' },
        font: { family: 'Inter, sans-serif', color: '#64748b', size: 11 }
      };

      Plotly.newPlot('chart-mensal', [traceLinha], layoutLinha, { responsive: true, displayModeBar: false });
    }

    // 3. Gráfico Top Produtos
    const resProd = await fetch('/api/dashboard/top-produtos');
    if (resProd.ok) {
      const dadosProd = await resProd.json();
      const nomes = dadosProd.map(d => d.nome.length > 20 ? d.nome.substring(0, 20) + '...' : d.nome);
      const qtds = dadosProd.map(d => d.qtd_vendida);

      const traceBarras = {
        x: nomes,
        y: qtds,
        type: 'bar',
        marker: { color: '#3b82f6' }
      };

      const layoutBarras = {
        margin: { l: 40, r: 20, t: 20, b: 80 },
        paper_bgcolor: 'rgba(0,0,0,0)',
        plot_bgcolor: 'rgba(0,0,0,0)',
        xaxis: { tickangle: -30, gridcolor: '#f1f5f9' },
        yaxis: { gridcolor: '#f1f5f9' },
        font: { family: 'Inter, sans-serif', color: '#64748b', size: 11 }
      };

      Plotly.newPlot('chart-produtos', [traceBarras], layoutBarras, { responsive: true, displayModeBar: false });
    }

  } catch (err) {
    console.error("Erro ao carregar dados do Dashboard:", err);
  }
}

// ==========================================
// TELA 2: ANALISTA IA (CHAT + HISTÓRICO)
// ==========================================
let chatHistory = [];
let conversaAtivaId = null;
let chatInicializado = false;
const reportStore = new Map();

function _escaparHtml(texto) {
  return String(texto || '')
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;');
}

function _obterHtmlBoasVindas() {
  return `
    <div class="flex gap-4 max-w-3xl">
      <div class="w-10 h-10 rounded-xl bg-gradient-to-tr from-blue-600 to-indigo-600 flex items-center justify-center text-white shrink-0 shadow-md">
        <i data-lucide="bot" class="w-5 h-5"></i>
      </div>
      <div class="space-y-1 w-full">
        <div class="flex items-center gap-2">
          <span class="font-bold text-slate-800 text-sm">DataMind AI</span>
          <span class="text-[11px] text-slate-400">Analista Oficial</span>
        </div>
        <div class="bg-slate-50 border border-slate-200/80 rounded-2xl rounded-tl-sm p-5 text-sm text-slate-700 leading-relaxed shadow-sm">
          Olá! Sou seu analista de inteligência empresarial. Estou conectado à base em tempo real através de consultas SQL controladas.<br><br>
          Você pode me fazer perguntas sobre faturamento, vendas, clientes, inadimplência e desempenho comercial.

          <div class="mt-4 pt-3 border-t border-slate-200">
            <span class="text-xs font-semibold text-slate-500 block mb-2">Exemplos de perguntas para começar:</span>
            <div class="flex flex-wrap gap-2">
              <button onclick="preencherPergunta('Quanto a empresa faturou no total em vendas concluídas?')" class="text-xs bg-white hover:bg-indigo-50 hover:border-indigo-300 text-slate-700 hover:text-indigo-700 px-3 py-1.5 rounded-lg border border-slate-200 shadow-sm transition font-medium">
                💰 Faturamento Total
              </button>
              <button onclick="preencherPergunta('Quais foram os cinco produtos mais vendidos em quantidade e gere um gráfico de barras?')" class="text-xs bg-white hover:bg-indigo-50 hover:border-indigo-300 text-slate-700 hover:text-indigo-700 px-3 py-1.5 rounded-lg border border-slate-200 shadow-sm transition font-medium">
                📊 Top 5 Produtos + Gráfico
              </button>
              <button onclick="preencherPergunta('Quais clientes estão com pagamentos atrasados e qual o valor total da inadimplência?')" class="text-xs bg-white hover:bg-indigo-50 hover:border-indigo-300 text-slate-700 hover:text-indigo-700 px-3 py-1.5 rounded-lg border border-slate-200 shadow-sm transition font-medium">
                ⚠️ Inadimplência Real
              </button>
              <button onclick="preencherPergunta('Qual vendedor teve o melhor desempenho em faturamento?')" class="text-xs bg-white hover:bg-indigo-50 hover:border-indigo-300 text-slate-700 hover:text-indigo-700 px-3 py-1.5 rounded-lg border border-slate-200 shadow-sm transition font-medium">
                🏆 Melhor Vendedor
              </button>
              <button onclick="preencherPergunta('Qual o ticket médio das vendas concluídas?')" class="text-xs bg-white hover:bg-indigo-50 hover:border-indigo-300 text-slate-700 hover:text-indigo-700 px-3 py-1.5 rounded-lg border border-slate-200 shadow-sm transition font-medium">
                🎯 Ticket Médio
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  `;
}

function _renderizarMensagemUsuario(texto) {
  const chatContainer = document.getElementById('chat-messages');
  const userMsgHtml = `
    <div class="flex gap-4 justify-end max-w-3xl ml-auto">
      <div class="bg-indigo-600 text-white rounded-2xl rounded-tr-sm p-4 text-sm shadow-md">
        ${_escaparHtml(texto)}
      </div>
      <div class="w-10 h-10 rounded-xl bg-slate-200 text-slate-700 flex items-center justify-center shrink-0">
        <i data-lucide="user" class="w-5 h-5"></i>
      </div>
    </div>
  `;
  chatContainer.insertAdjacentHTML('beforeend', userMsgHtml);
}

function _renderizarMensagemAssistente({ pergunta, resposta, dados_tabela, grafico, intencao }) {
  const chatContainer = document.getElementById('chat-messages');
  const msgId = 'msg-' + Date.now() + '-' + Math.floor(Math.random() * 10000);
  const chartContainerId = 'chart-' + msgId;
  const respostaFormatada = marked.parse(resposta || '');

  reportStore.set(msgId, {
    pergunta: pergunta || '',
    resposta: resposta || '',
    dados_tabela: dados_tabela || [],
    grafico: grafico || null,
    chartContainerId
  });

  let chartBlockHtml = '';
  if (grafico) {
    chartBlockHtml = `
      <div class="mt-4 p-4 bg-slate-50 border border-slate-200 rounded-xl overflow-hidden">
        <div id="${chartContainerId}" style="width: 100%; height: 320px;"></div>
      </div>
    `;
  }

  let exportBarHtml = '';
  const ehRespostaAnalitica = intencao !== 'esclarecimento' && intencao !== 'conversa_geral';
  if (ehRespostaAnalitica) {
    const temTabela = Array.isArray(dados_tabela) && dados_tabela.length > 0;
    const temGrafico = Boolean(grafico);
    exportBarHtml = `
      <div class="mt-4 pt-3 border-t border-slate-100 flex flex-wrap items-center gap-2 not-prose">
        <button onclick="exportarPDF('${msgId}', this)" class="inline-flex items-center gap-1.5 text-xs font-medium px-3 py-1.5 rounded-lg bg-indigo-50 text-indigo-700 hover:bg-indigo-100 border border-indigo-200/80 transition">
          <i data-lucide="file-text" class="w-3.5 h-3.5"></i>
          <span>Exportar PDF</span>
        </button>
        ${temTabela ? `
          <button onclick="exportarCSV('${msgId}')" class="inline-flex items-center gap-1.5 text-xs font-medium px-3 py-1.5 rounded-lg bg-emerald-50 text-emerald-700 hover:bg-emerald-100 border border-emerald-200/80 transition">
            <i data-lucide="table" class="w-3.5 h-3.5"></i>
            <span>Exportar CSV</span>
          </button>
        ` : ''}
        ${temGrafico ? `
          <button onclick="exportarPNG('${msgId}')" class="inline-flex items-center gap-1.5 text-xs font-medium px-3 py-1.5 rounded-lg bg-slate-100 text-slate-700 hover:bg-slate-200 border border-slate-200 transition">
            <i data-lucide="image" class="w-3.5 h-3.5"></i>
            <span>Baixar PNG</span>
          </button>
        ` : ''}
      </div>
    `;
  }

  const botMsgHtml = `
    <div id="${msgId}" class="flex gap-4 max-w-3xl w-full">
      <div class="w-10 h-10 rounded-xl bg-gradient-to-tr from-blue-600 to-indigo-600 flex items-center justify-center text-white shrink-0 shadow-md">
        <i data-lucide="bot" class="w-5 h-5"></i>
      </div>
      <div class="space-y-1.5 w-full min-w-0">
        <div class="flex items-center gap-2">
          <span class="font-bold text-slate-800 text-sm">DataMind AI</span>
          <span class="text-[10px] bg-indigo-50 text-indigo-700 px-2 py-0.5 rounded-full font-semibold border border-indigo-200">Analista Oficial</span>
        </div>
        <div class="bg-white border border-slate-200/90 rounded-2xl rounded-tl-sm p-5 text-sm text-slate-800 shadow-sm leading-relaxed prose max-w-none">
          <div>${respostaFormatada}</div>
          ${chartBlockHtml}
          ${exportBarHtml}
        </div>
      </div>
    </div>
  `;

  chatContainer.insertAdjacentHTML('beforeend', botMsgHtml);

  if (grafico) {
    Plotly.newPlot(chartContainerId, grafico.data, grafico.layout, grafico.config);
  }
}

async function carregarListaConversas() {
  const listEl = document.getElementById('chat-history-list');
  if (!listEl) return [];

  try {
    const res = await fetch('/api/conversas');
    if (!res.ok) throw new Error('Falha ao listar conversas');
    const conversas = await res.json();

    if (conversas.length === 0) {
      listEl.innerHTML = `<p class="text-xs text-slate-400 text-center py-6 px-3">Nenhuma conversa salva ainda. Envie sua primeira pergunta!</p>`;
      return [];
    }

    listEl.innerHTML = conversas.map(c => {
      const ativa = c.id === conversaAtivaId;
      const classeCard = ativa
        ? 'bg-indigo-50 border-indigo-200 text-indigo-900'
        : 'bg-transparent border-transparent text-slate-700 hover:bg-slate-50';
      const dataCurta = (c.atualizada_em || '').slice(0, 16).replace('T', ' ');
      return `
        <div onclick="selecionarConversa(${c.id})" class="group flex items-start justify-between gap-2 p-2.5 rounded-xl border cursor-pointer transition ${classeCard}">
          <div class="min-w-0 flex-1">
            <p class="text-xs font-semibold truncate">${_escaparHtml(c.titulo)}</p>
            <p class="text-[10px] text-slate-400 mt-0.5">${dataCurta}</p>
          </div>
          <button onclick="excluirConversaUI(event, ${c.id})" title="Excluir conversa" class="opacity-0 group-hover:opacity-100 p-1 rounded-md text-slate-400 hover:text-rose-600 hover:bg-rose-50 transition shrink-0">
            <i data-lucide="trash-2" class="w-3.5 h-3.5"></i>
          </button>
        </div>
      `;
    }).join('');

    lucide.createIcons();
    return conversas;
  } catch (err) {
    listEl.innerHTML = `<p class="text-xs text-rose-500 text-center py-4">Erro ao carregar histórico.</p>`;
    return [];
  }
}

async function selecionarConversa(conversaId) {
  const chatContainer = document.getElementById('chat-messages');
  try {
    const res = await fetch(`/api/conversas/${conversaId}`);
    if (!res.ok) {
      iniciarNovaConversa();
      return;
    }
    const conversa = await res.json();
    conversaAtivaId = conversa.id;
    localStorage.setItem('datamind_active_conversa_id', String(conversa.id));

    chatHistory = [];
    reportStore.clear();
    chatContainer.innerHTML = _obterHtmlBoasVindas();

    let ultimaPergunta = '';
    for (const m of conversa.mensagens || []) {
      chatHistory.push({ role: m.role, content: m.conteudo });
      if (m.role === 'user') {
        ultimaPergunta = m.conteudo;
        _renderizarMensagemUsuario(m.conteudo);
      } else {
        _renderizarMensagemAssistente({
          pergunta: ultimaPergunta,
          resposta: m.conteudo,
          dados_tabela: m.dados_tabela,
          grafico: m.grafico,
          intencao: m.intencao
        });
      }
    }

    lucide.createIcons();
    await carregarListaConversas();
    setTimeout(() => {
      chatContainer.scrollTop = chatContainer.scrollHeight;
    }, 120);
  } catch (err) {
    console.error('Erro ao abrir conversa:', err);
  }
}

function iniciarNovaConversa() {
  conversaAtivaId = null;
  localStorage.removeItem('datamind_active_conversa_id');
  chatHistory = [];
  reportStore.clear();
  const chatContainer = document.getElementById('chat-messages');
  if (chatContainer) {
    chatContainer.innerHTML = _obterHtmlBoasVindas();
  }
  lucide.createIcons();
  carregarListaConversas();
  document.getElementById('input-pergunta')?.focus();
}

async function excluirConversaUI(event, conversaId) {
  event.stopPropagation();
  try {
    const res = await fetch(`/api/conversas/${conversaId}`, { method: 'DELETE' });
    if (!res.ok) return;
    if (conversaAtivaId === conversaId) {
      iniciarNovaConversa();
    } else {
      await carregarListaConversas();
    }
  } catch (err) {
    console.error('Erro ao excluir conversa:', err);
  }
}

async function inicializarAreaChat() {
  const conversas = await carregarListaConversas();
  if (chatInicializado) return;
  chatInicializado = true;

  const salvaId = parseInt(localStorage.getItem('datamind_active_conversa_id') || '', 10);
  if (salvaId && conversas.some(c => c.id === salvaId)) {
    await selecionarConversa(salvaId);
  } else if (conversas.length > 0) {
    await selecionarConversa(conversas[0].id);
  } else {
    iniciarNovaConversa();
  }
}

function preencherPergunta(texto) {
  const input = document.getElementById('input-pergunta');
  input.value = texto;
  input.focus();
}

async function enviarPergunta() {
  const input = document.getElementById('input-pergunta');
  const pergunta = input.value.trim();
  if (!pergunta) return;

  const chatContainer = document.getElementById('chat-messages');

  // 1. Mensagem do Usuário
  _renderizarMensagemUsuario(pergunta);
  input.value = '';
  lucide.createIcons();

  // 2. Indicador de Carregamento da IA
  const loadingId = 'loading-' + Date.now();
  const loadingHtml = `
    <div id="${loadingId}" class="flex gap-4 max-w-3xl">
      <div class="w-10 h-10 rounded-xl bg-gradient-to-tr from-blue-600 to-indigo-600 flex items-center justify-center text-white shrink-0 shadow-md">
        <i data-lucide="bot" class="w-5 h-5"></i>
      </div>
      <div class="bg-slate-50 border border-slate-200/80 rounded-2xl rounded-tl-sm p-4 text-sm text-slate-600 flex items-center gap-3">
        <span class="w-2 h-2 rounded-full bg-indigo-600 animate-ping"></span>
        <span>Consultando banco de dados com segurança e analisando...</span>
      </div>
    </div>
  `;
  chatContainer.insertAdjacentHTML('beforeend', loadingHtml);
  chatContainer.scrollTop = chatContainer.scrollHeight;
  lucide.createIcons();

  const btnEnviar = document.getElementById('btn-enviar');
  btnEnviar.disabled = true;

  try {
    const res = await fetch('/api/chat', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        pergunta,
        conversa_id: conversaAtivaId,
        historico: chatHistory.slice(-10)
      })
    });

    const data = await res.json();
    document.getElementById(loadingId)?.remove();

    if (data.sucesso) {
      if (data.conversa_id) {
        conversaAtivaId = data.conversa_id;
        localStorage.setItem('datamind_active_conversa_id', String(conversaAtivaId));
      }

      chatHistory.push({ role: 'user', content: pergunta });
      chatHistory.push({ role: 'assistant', content: data.resposta || '' });

      _renderizarMensagemAssistente({
        pergunta,
        resposta: data.resposta || '',
        dados_tabela: data.dados_tabela || [],
        grafico: data.grafico || null,
        intencao: data.intencao
      });

      await carregarListaConversas();

      setTimeout(() => {
        chatContainer.scrollTop = chatContainer.scrollHeight;
      }, 150);

    } else {
      const errorMsgHtml = `
        <div class="flex gap-4 max-w-3xl">
          <div class="w-10 h-10 rounded-xl bg-rose-600 flex items-center justify-center text-white shrink-0 shadow-md">
            <i data-lucide="alert-octagon" class="w-5 h-5"></i>
          </div>
          <div class="bg-rose-50 border border-rose-200 rounded-2xl rounded-tl-sm p-4 text-sm text-rose-700">
            <strong>Não foi possível processar a consulta:</strong><br>
            ${data.mensagem || data.erro}
          </div>
        </div>
      `;
      chatContainer.insertAdjacentHTML('beforeend', errorMsgHtml);
    }

  } catch (err) {
    document.getElementById(loadingId)?.remove();
    const errorMsgHtml = `
      <div class="flex gap-4 max-w-3xl">
        <div class="w-10 h-10 rounded-xl bg-rose-600 flex items-center justify-center text-white shrink-0 shadow-md">
          <i data-lucide="alert-octagon" class="w-5 h-5"></i>
        </div>
        <div class="bg-rose-50 border border-rose-200 rounded-2xl rounded-tl-sm p-4 text-sm text-rose-700">
          Erro de comunicação com o servidor: ${err.message}
        </div>
      </div>
    `;
    chatContainer.insertAdjacentHTML('beforeend', errorMsgHtml);
  } finally {
    btnEnviar.disabled = false;
    chatContainer.scrollTop = chatContainer.scrollHeight;
    lucide.createIcons();
  }
}

// Enter para enviar
document.getElementById('input-pergunta')?.addEventListener('keydown', (e) => {
  if (e.key === 'Enter') enviarPergunta();
});

// ==========================================
// EXPORTAÇÃO DE RELATÓRIOS (PDF, CSV, PNG)
// ==========================================
function _baixarBlob(blob, nomeArquivo) {
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = nomeArquivo;
  document.body.appendChild(a);
  a.click();
  a.remove();
  setTimeout(() => URL.revokeObjectURL(url), 1000);
}

async function exportarPDF(msgId, btnEl) {
  const item = reportStore.get(msgId);
  if (!item) return;

  const textoOriginal = btnEl ? btnEl.innerHTML : '';
  if (btnEl) {
    btnEl.disabled = true;
    btnEl.innerHTML = '<span>Gerando PDF...</span>';
  }

  try {
    let graficoBase64 = null;
    if (item.grafico) {
      const chartEl = document.getElementById(item.chartContainerId);
      if (chartEl && typeof Plotly !== 'undefined') {
        graficoBase64 = await Plotly.toImage(chartEl, {
          format: 'png',
          width: 960,
          height: 480,
          scale: 2
        });
      }
    }

    const res = await fetch('/api/export/pdf', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        pergunta: item.pergunta,
        resposta: item.resposta,
        dados_tabela: item.dados_tabela,
        grafico_imagem_base64: graficoBase64
      })
    });

    if (!res.ok) throw new Error('Falha ao gerar o PDF no servidor.');

    const pdfBlob = await res.blob();
    const stamp = new Date().toISOString().slice(0, 16).replace(/[:T]/g, '-');
    _baixarBlob(pdfBlob, `relatorio-datamind-${stamp}.pdf`);
  } catch (err) {
    console.error('Erro ao exportar PDF:', err);
    alert('Não foi possível exportar o PDF: ' + err.message);
  } finally {
    if (btnEl) {
      btnEl.disabled = false;
      btnEl.innerHTML = textoOriginal;
      lucide.createIcons();
    }
  }
}

function exportarCSV(msgId) {
  const item = reportStore.get(msgId);
  if (!item || !item.dados_tabela || item.dados_tabela.length === 0) return;

  const colunas = Object.keys(item.dados_tabela[0]);
  const escaparCelula = (val) => {
    const texto = val === null || val === undefined ? '' : String(val);
    return `"${texto.replace(/"/g, '""')}"`;
  };

  const linhas = [
    colunas.map(escaparCelula).join(';'),
    ...item.dados_tabela.map(row => colunas.map(col => escaparCelula(row[col])).join(';'))
  ];

  // BOM UTF-8 para abrir com acentos corretos no Excel em português
  const csvConteudo = '\uFEFF' + linhas.join('\r\n');
  const blob = new Blob([csvConteudo], { type: 'text/csv;charset=utf-8;' });
  const stamp = new Date().toISOString().slice(0, 16).replace(/[:T]/g, '-');
  _baixarBlob(blob, `datamind-dados-${stamp}.csv`);
}

async function exportarPNG(msgId) {
  const item = reportStore.get(msgId);
  if (!item || !item.grafico) return;

  const chartEl = document.getElementById(item.chartContainerId);
  if (!chartEl || typeof Plotly === 'undefined') return;

  const stamp = new Date().toISOString().slice(0, 16).replace(/[:T]/g, '-');
  await Plotly.downloadImage(chartEl, {
    format: 'png',
    width: 1000,
    height: 550,
    scale: 2,
    filename: `datamind-grafico-${stamp}`
  });
}

// ==========================================
// TELA 3: AUDITORIA
// ==========================================
async function carregarAuditoria() {
  const tbody = document.getElementById('audit-table-body');
  try {
    const res = await fetch('/api/audit');
    if (!res.ok) throw new Error("Falha ao carregar auditoria");
    const logs = await res.json();

    if (logs.length === 0) {
      tbody.innerHTML = `<tr><td colspan="6" class="py-6 text-center text-slate-400">Nenhum registro de auditoria encontrado.</td></tr>`;
      return;
    }

    tbody.innerHTML = logs.map(l => {
      let badge = '';
      if (l.status === 'APROVADO') {
        badge = `<span class="bg-emerald-50 text-emerald-700 px-2 py-0.5 rounded-full font-semibold border border-emerald-200 text-[10px]">APROVADO</span>`;
      } else if (l.status === 'BLOQUEADO') {
        badge = `<span class="bg-rose-50 text-rose-700 px-2 py-0.5 rounded-full font-semibold border border-rose-200 text-[10px]">BLOQUEADO</span>`;
      } else {
        badge = `<span class="bg-amber-50 text-amber-700 px-2 py-0.5 rounded-full font-semibold border border-amber-200 text-[10px]">ERRO</span>`;
      }

      return `
        <tr class="hover:bg-slate-50/80 transition">
          <td class="py-3 px-4 font-mono text-[11px] text-slate-500">${l.data_hora}</td>
          <td class="py-3 px-4 font-medium text-slate-800">${l.pergunta_usuario || '-'}</td>
          <td class="py-3 px-4 font-mono text-[11px] text-slate-600 max-w-xs truncate" title="${l.sql_proposto}">${l.sql_proposto}</td>
          <td class="py-3 px-4">${badge}</td>
          <td class="py-3 px-4 font-mono text-[11px]">${l.tempo_execucao_ms ? l.tempo_execucao_ms + ' ms' : '-'}</td>
          <td class="py-3 px-4 font-mono text-[11px]">${l.linhas_retornadas ?? '-'}</td>
        </tr>
      `;
    }).join('');

  } catch (err) {
    tbody.innerHTML = `<tr><td colspan="6" class="py-6 text-center text-rose-500">Erro: ${err.message}</td></tr>`;
  }
}

// Inicialização (restaura a última aba visitada e a conversa ativa)
document.addEventListener('DOMContentLoaded', () => {
  lucide.createIcons();
  const ultimaAba = localStorage.getItem('datamind_active_view');
  if (ultimaAba && ['dashboard', 'chat', 'audit'].includes(ultimaAba)) {
    navegarPara(ultimaAba);
  } else {
    carregarDashboard();
  }
});
