import os, datetime, pathlib, sys
import google.generativeai as genai

api_key = os.environ.get("GEMINI_API_KEY")
if not api_key:
    print("ERRO: Variavel GEMINI_API_KEY nao encontrada.")
    sys.exit(1)

genai.configure(api_key=api_key)
model = genai.GenerativeModel("gemini-2.0-flash")

ARQUIVOS = [
    "web/app.py",
    "web/onboarding.py",
    "web/ia_gemini.py",
    "web/zapi.py",
    "database_gcp.py",
    "cal_forense/calendar_resolver.py",
    "requirements.txt",
    "Dockerfile",
]

def ler_arquivos():
    partes = []
    for path in ARQUIVOS:
        if os.path.exists(path):
            try:
                with open(path, "r", encoding="utf-8") as f:
                    conteudo = f.read()
                partes.append(f"### ARQUIVO: {path}\n```python\n{conteudo}\n```")
            except Exception as e:
                print(f"Aviso: Erro ao ler {path}: {e}")
    return "\n\n".join(partes)

PROMPT_SISTEMA = """Voce e um Engenheiro de Software Senior e Documentador Tecnico.
Com base EXCLUSIVAMENTE nos codigos do projeto Prazu fornecidos, gere documentacao tecnica completa em Markdown cobrindo:
1. Visao geral do produto
2. Arquitetura e servicos (Cloud Run, Cloud SQL, Z-API, Gemini)
3. Logica de calculo de prazos (calendar_resolver.py)
4. Fluxo do usuario (cadastro, onboarding, dashboard, configuracoes)
5. Banco de dados (tabelas e colunas principais)
6. Dependencias, variaveis de ambiente, deploy e jobs automaticos

ARQUIVOS DO PROJETO:
{codigo}"""

def gerar():
    codigo = ler_arquivos()
    if not codigo:
        return "Erro: Nenhum arquivo encontrado."
    print(f"Enviando {len(codigo)} caracteres para o Gemini...")
    response = model.generate_content(PROMPT_SISTEMA.format(codigo=codigo))
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
