#!/usr/bin/env python3
"""
fix_credentials.py — adiciona credentials: 'include' em todos os fetch do onboarding.html
Aplicar: cd ~/prazu && python3 fix_credentials.py
"""
from pathlib import Path
import subprocess

FILE = Path("web/templates/onboarding.html")
src = FILE.read_text()

OLD = "method: 'POST',"
NEW = "method: 'POST',\n      credentials: 'include',"

count = src.count(OLD)
print(f"Fetches encontrados: {count}")

src = src.replace(OLD, NEW)
FILE.write_text(src)

# Verificar
count_new = src.count("credentials: 'include'")
print(f"credentials: 'include' inseridos: {count_new}")
print("✅ Pronto")
