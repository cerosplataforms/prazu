#!/usr/bin/env python3
"""
fix_djen_silencioso.py — remove envios de WhatsApp do _buscar_djen
A busca DJEN deve ser silenciosa — sem mensagens de status ou erro.
Aplicar: cd ~/prazu && python3 fix_djen_silencioso.py
"""
from pathlib import Path
import subprocess

F = Path("web/onboarding.py")
src = F.read_text()

# Remove mensagem "nenhuma publicacao encontrada"
OLD1 = '''        if not comunicacoes:
            if phone:
                await _zapi_client.enviar(phone, "Nenhuma publicacao encontrada no DJEN nos ultimos 90 dias.")
            return'''
NEW1 = '''        if not comunicacoes:
            return'''

# Remove mensagem de sucesso ao final
OLD2 = '''        if phone:
            msg = f"Busca DJEN concluida! {len(numeros_cnj)} processo(s) encontrado(s), {novos} novo(s) importado(s)."
            if erros:
                msg += f" {erros} sem dados no DataJud."
            msg += " Acesse o dashboard para ver seus prazos."
            await _zapi_client.enviar(phone, msg)
        log.info(f"_buscar_djen OK: {novos} novos, {erros} erros")'''
NEW2 = '''        log.info(f"_buscar_djen OK: {novos} novos, {erros} erros")'''

# Remove mensagem de erro
OLD3 = '''    except Exception as e:
        log.error(f"_buscar_djen erro: {e}", exc_info=True)
        if phone:
            try:
                await _zapi_client.enviar(phone, "Erro ao buscar processos. Tente novamente em alguns minutos.")'''
NEW3 = '''    except Exception as e:
        log.error(f"_buscar_djen erro: {e}", exc_info=True)
        if False:
            try:
                pass  # mensagens de erro DJEN removidas — busca é silenciosa'''

ok = True
for i, (old, new) in enumerate([(OLD1, NEW1), (OLD2, NEW2), (OLD3, NEW3)], 1):
    if old in src:
        src = src.replace(old, new)
        print(f"✅ Fix {i} aplicado")
    else:
        print(f"❌ Fix {i} não encontrado")
        ok = False

if ok:
    F.write_text(src)
    r = subprocess.run(["python3", "-m", "py_compile", "web/onboarding.py"], capture_output=True, text=True)
    print(f"{'✅ Sintaxe OK' if r.returncode == 0 else '❌ Erro: ' + r.stderr}")
else:
    print("⚠️  Alguns trechos não encontrados — verifique manualmente")
