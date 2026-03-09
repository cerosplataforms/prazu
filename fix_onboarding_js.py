#!/usr/bin/env python3
"""
fix_onboarding_js.py — corrige JS do onboarding.html
1. Etapa 1: valida OAB via API antes de avançar
2. Adiciona botão voltar na etapa 3
3. Desabilita botão após primeiro clique para evitar duplo submit
Aplicar: cd ~/prazu && python3 fix_onboarding_js.py
"""
from pathlib import Path

F = Path("web/templates/onboarding.html")
src = F.read_text()

# ── Fix 1: botão voltar na etapa 3 ────────────────────────────────────────
OLD_BTN3 = '''    <button class="btn-primary" id="btnFinalizar">
      <span class="spinner"></span>
      <span>Concluir configuração 🎉</span>
    </button>'''

NEW_BTN3 = '''    <button class="btn-secondary" id="btnVoltarStep3" style="margin-bottom:.5rem" onclick="goStep(2);document.getElementById('phase-code').style.display='none';document.getElementById('phase-number').style.display='block';">← Voltar</button>
    <button class="btn-primary" id="btnFinalizar">
      <span class="spinner"></span>
      <span>Concluir configuração 🎉</span>
    </button>'''

if OLD_BTN3 in src:
    src = src.replace(OLD_BTN3, NEW_BTN3)
    print("✅ Botão voltar etapa 3 adicionado")
else:
    print("❌ Botão finalizar não encontrado")

# ── Fix 2: botão voltar na etapa 2 (fase número) ──────────────────────────
OLD_BTN2 = '''      <button class="btn-primary" id="btnEnviarCodigo">
        <span class="spinner"></span>
        <span>Enviar código</span>
      </button>'''

NEW_BTN2 = '''      <button class="btn-secondary" id="btnVoltarStep2" style="margin-bottom:.5rem" onclick="goStep(1);">← Voltar</button>
      <button class="btn-primary" id="btnEnviarCodigo">
        <span class="spinner"></span>
        <span>Enviar código</span>
      </button>'''

if OLD_BTN2 in src:
    src = src.replace(OLD_BTN2, NEW_BTN2)
    print("✅ Botão voltar etapa 2 adicionado")
else:
    print("❌ Botão enviar código não encontrado")

# ── Fix 3: validação OAB via API na etapa 1 ───────────────────────────────
OLD_STEP1_JS = '''  state.oab_numero = num;
  state.oab_seccional = uf;
  state.tratamento = document.getElementById('tratamento').value;

  goStep(2);
});'''

NEW_STEP1_JS = '''  state.oab_numero = num;
  state.oab_seccional = uf;
  state.tratamento = document.getElementById('tratamento').value;

  // Verificar OAB duplicada antes de avançar
  setLoading('btnStep1', true);
  try {
    const res = await fetch('/api/onboarding/verificar-oab', {
      method: 'POST',
      credentials: 'include',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ oab_numero: num, oab_seccional: uf })
    });
    const data = await res.json();
    if (res.ok) {
      goStep(2);
    } else if (res.status === 409) {
      showAlert('step1',
        `⚠️ ${data.detail} <a href="mailto:suporte@prazu.com.br" style="color:inherit;font-weight:600">Contatar suporte →</a>`,
        'warning'
      );
      document.getElementById('support-step1').classList.add('visible');
    } else {
      showAlert('step1', data.detail || 'Erro ao verificar OAB.', 'error');
    }
  } catch(e) {
    showAlert('step1', 'Erro de conexão. Verifique sua internet.', 'error');
  } finally {
    setLoading('btnStep1', false);
  }
});'''

if OLD_STEP1_JS in src:
    src = src.replace(OLD_STEP1_JS, NEW_STEP1_JS)
    print("✅ Validação OAB via API na etapa 1 adicionada")
else:
    print("❌ Trecho JS etapa 1 não encontrado")

F.write_text(src)
print("\nFeito. Verifique o resultado.")
