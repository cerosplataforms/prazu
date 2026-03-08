import os, datetime, pathlib, sys
from google import genai

api_key = os.environ.get("GEMINI_API_KEY")
if not api_key:
    print("ERRO: GEMINI_API_KEY nao encontrada.")
    sys.exit(1)

client = genai.Client(api_key=api_key)

ARQUIVOS = [
    "web/app.py",
    "web/onboarding.py",
    "web/ia_gemini.py",
    "web/zapi.py",
    "database_gcp.py",
    "cal_forense/calendar_resolver.py",
    "Dockerfile",
]

def ler_arquivos():
    partes = []
    for path in ARQUIVOS:
        if os.path.exists(path):
            with open(path, "r", encoding="utf-8") as f:
                conteudo = f.read()[:5000]
            partes.append(f"### ARQUIVO: {path}\n```python\n{conteudo}\n```")
    return "\n\n".join(partes)

PROMPT = """Voce e um Documentador Tecnico Senior. Com base nos codigos do projeto Prazu,
gere documentacao tecnica completa em Markdown cobrindo:
1. Visao geral e arquitetura (Cloud Run, Cloud SQL, Z-API, Gemini)
2. Logica de calculo de prazos (calendar_resolver.py)
3. Fluxo do usuario (cadastro, onboarding, dashboard, configuracoes)
4. Banco de dados, variaveis de ambiente, deploy e jobs automaticos
Use linguagem tecnica clara com headers, tabelas e blocos de codigo."""

def gerar():
    codigo = ler_arquivos()
    print(f"Enviando {len(codigo)} caracteres para o Gemini...")
    response = client.models.generate_content(
        model="gemini-2.0-flash",
        contents=f"{PROMPT}\n\nARQUIVOS:\n{codigo}"
    )
    return response.text

def salvar(conteudo):
    now = datetime.datetime.now()
    docs = pathlib.Path("docs")
    docs.mkdir(exist_ok=True)
    (docs / "README.md").write_text(conteudo, encoding="utf-8")
    historico = docs / "historico"
    historico.mkdir(exist_ok=True)
    nome = now.strftime("%Y-%m-%d_%H-%M") + ".md"
    (historico / nome).write_text(conteudo, encoding="utf-8")
    print(f"Salvo: docs/README.md e docs/historico/{nome}")

if __name__ == "__main__":
    try:
        salvar(gerar())
    except Exception as e:
        print(f"Erro fatal: {e}")
        sys.exit(1)
