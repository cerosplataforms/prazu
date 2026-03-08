"""
Patch: atualiza vara e comarca dos processos que estão vazios no banco.
Roda via Cloud SQL Proxy.

Uso:
  ~/cloud-sql-proxy --port 5433 prazu-prod:southamerica-east1:prazu-db &
  PGPASSWORD='Prazu@2026!' python3 patch_vara_comarca.py
"""
import asyncio
import asyncpg
import re
import sys
sys.path.insert(0, '/Users/tatymesquita/prazu')

DB_DSN = dict(host="localhost", port=5433, user="prazu_user", password="Prazu@2026!", database="prazu")

def extrair_comarca(vara):
    if not vara or vara == "N/I":
        return ""
    m = re.search(r"[Cc]omarca\s+de\s+([A-ZÀ-Ú][^,/\-]+?)(?:\s*[,/\-]|$)", vara)
    if m:
        return m.group(1).strip().rstrip(".")
    m = re.search(r"\bde\s+([A-ZÀ-Ú][a-zà-ú]+(?:\s+[A-ZÀ-Ú][a-zà-ú]+)*)", vara)
    if m:
        return m.group(1).strip().rstrip(".")
    parts = vara.split(" - ")
    if len(parts) >= 2:
        last = parts[-1].strip()
        if last and last[0].isupper() and len(last) > 3:
            return last.rstrip(".")
    return ""

async def main():
    from datajud import consultar_processo

    conn = await asyncpg.connect(**DB_DSN)

    # Busca processos sem vara
    rows = await conn.fetch(
        "SELECT id, numero FROM processos WHERE vara IS NULL OR vara = '' OR comarca IS NULL OR comarca = ''"
    )
    print(f"{len(rows)} processo(s) para atualizar")

    for row in rows:
        pid, numero = row['id'], row['numero']
        print(f"\n→ {numero}")
        try:
            dados = consultar_processo(numero)
            if not dados:
                print(f"  DataJud: não encontrado")
                continue
            vara = dados.get("vara", "")
            comarca = extrair_comarca(vara)
            partes_ativo = ", ".join(dados.get("partes_ativo", []))
            partes_passivo = ", ".join(dados.get("partes_passivo", []))
            partes = f"{partes_ativo} vs {partes_passivo}" if partes_ativo and partes_passivo else partes_ativo or partes_passivo or ""
            tribunal = dados.get("tribunal", "")

            await conn.execute("""
                UPDATE processos SET
                    vara = COALESCE(NULLIF($1,''), vara),
                    comarca = COALESCE(NULLIF($2,''), comarca),
                    tribunal = COALESCE(NULLIF($3,''), tribunal),
                    partes = CASE WHEN (partes IS NULL OR partes = '' OR partes = 'N/I') AND $4 != '' THEN $4 ELSE partes END
                WHERE id = $5
            """, vara, comarca, tribunal, partes, pid)

            print(f"  vara:    {vara}")
            print(f"  comarca: {comarca}")
            print(f"  partes:  {partes or '(sem partes no DataJud)'}")
        except Exception as e:
            print(f"  ERRO: {e}")

    await conn.close()
    print("\n✅ Patch concluído!")

asyncio.run(main())
