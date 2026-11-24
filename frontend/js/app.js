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

  if (tela === 'dashboard') {
    titleEl.innerText = "Dashboard Executivo";
    subEl.innerText = "Acompanhe métricas em tempo real e converse com os dados.";
    carregarDashboard();
  } else if (tela === 'chat') {
    titleEl.innerText = "Analista de IA Corporativo";
    subEl.innerText = "Faça perguntas em linguagem natural diretamente para a base de dados.";
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
// TELA 2: ANALISTA IA (CHAT)
// ==========================================
const chatHistory = [];

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
  const userMsgHtml = `
    <div class="flex gap-4 justify-end max-w-3xl ml-auto">
      <div class="bg-indigo-600 text-white rounded-2xl rounded-tr-sm p-4 text-sm shadow-md">
        ${pergunta}
      </div>
      <div class="w-10 h-10 rounded-xl bg-slate-200 text-slate-700 flex items-center justify-center shrink-0">
        <i data-lucide="user" class="w-5 h-5"></i>
      </div>
    </div>
  `;
  chatContainer.insertAdjacentHTML('beforeend', userMsgHtml);
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
        historico: chatHistory.slice(-10)
      })
    });

    const data = await res.json();
    document.getElementById(loadingId)?.remove();

    if (data.sucesso) {
      chatHistory.push({ role: 'user', content: pergunta });
      chatHistory.push({ role: 'assistant', content: data.resposta || '' });

      const chartContainerId = 'chart-msg-' + Date.now();
      const respostaFormatada = marked.parse(data.resposta || '');

      let chartBlockHtml = '';
      if (data.grafico) {
        chartBlockHtml = `
          <div class="mt-4 p-4 bg-slate-50 border border-slate-200 rounded-xl overflow-hidden">
            <div id="${chartContainerId}" style="width: 100%; height: 260px;"></div>
          </div>
        `;
      }

      const botMsgHtml = `
        <div id="msg-${data.tempo_ms}" class="flex gap-4 max-w-3xl w-full">
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
            </div>
          </div>
        </div>
      `;

      chatContainer.insertAdjacentHTML('beforeend', botMsgHtml);

      // Renderiza gráfico se existir
      if (data.grafico) {
        Plotly.newPlot(chartContainerId, data.grafico.data, data.grafico.layout, data.grafico.config);
      }

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

// Inicialização
document.addEventListener('DOMContentLoaded', () => {
  lucide.createIcons();
  carregarDashboard();
});
