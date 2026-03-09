#!/usr/bin/env python3
from pathlib import Path

F = Path("web/templates/configuracoes.html")
lines = F.read_text().splitlines()

for i, line in enumerate(lines):
    if 'type="text" id="comarca"' in line and not line.strip().startswith('<input'):
        lines[i] = '          <input type="text" id="comarca" value="{{ advogado.comarca or \'\' }}" placeholder="Ex: Belo Horizonte">'
        print(f"✅ Linha {i+1} corrigida")
        break

F.write_text("\n".join(lines) + "\n")
print("Feito")
