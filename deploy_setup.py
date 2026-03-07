#!/usr/bin/env python3
"""
Deploy do Prazu no Cloud Run.
Roda da pasta ~/prazu: python3 deploy_setup.py
"""
import subprocess, sys, os

PROJECT = "prazu-prod"
REGION = "southamerica-east1"
SERVICE = "prazu"
IMAGE = f"gcr.io/{PROJECT}/{SERVICE}"
INSTANCE = "prazu-prod:southamerica-east1:prazu-db"

def run(cmd, check=True):
    print(f"\n$ {cmd}")
    result = subprocess.run(cmd, shell=True, capture_output=False)
    if check and result.returncode != 0:
        print(f"❌ Erro no comando acima")
        sys.exit(1)
    return result.returncode

print("=" * 60)
print("🚀 DEPLOY PRAZU — Cloud Run")
print("=" * 60)

run("gcloud config set project prazu-prod")

print("\n→ Habilitando APIs...")
run("gcloud services enable run.googleapis.com cloudbuild.googleapis.com secretmanager.googleapis.com sqladmin.googleapis.com --project=prazu-prod")

if not os.path.exists("Dockerfile"):
    print("\n→ Criando Dockerfile...")
    dockerfile = '''FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
EXPOSE 8080
CMD ["uvicorn", "web.app:app", "--host", "0.0.0.0", "--port", "8080"]
'''
    open("Dockerfile", "w").write(dockerfile)
    print("  ✅ Dockerfile criado")

if not os.path.exists(".dockerignore"):
    dockerignore = '''.env
__pycache__
*.pyc
*.db
.git
calendar.db
'''
    open(".dockerignore", "w").write(dockerignore)
    print("  ✅ .dockerignore criado")

print(f"\n→ Build da imagem {IMAGE}...")
run(f"gcloud builds submit --tag {IMAGE} --project={PROJECT}")

print("\n→ Buscando conta de serviço...")
result = subprocess.run(
    f"gcloud iam service-accounts list --project={PROJECT} --format='value(email)' --filter='displayName:Compute Engine'",
    shell=True, capture_output=True, text=True
)
sa = result.stdout.strip().split('\n')[0] if result.stdout.strip() else ""
if not sa:
    # pega numero do projeto e monta SA padrão
    r2 = subprocess.run(f"gcloud projects describe {PROJECT} --format='value(projectNumber)'", shell=True, capture_output=True, text=True)
    num = r2.stdout.strip()
    sa = f"{num}-compute@developer.gserviceaccount.com"
print(f"  Conta de serviço: {sa}")

print("\n→ Configurando permissões de secrets...")
secrets = ["db-password", "db-user", "db-host", "db-name", "jwt-secret", "gemini-api-key", "scheduler-secret", "evolution-api-key"]
for secret in secrets:
    run(f'gcloud secrets add-iam-policy-binding {secret} --member="serviceAccount:{sa}" --role="roles/secretmanager.secretAccessor" --project={PROJECT}', check=False)

print(f"\n→ Deployando {SERVICE} no Cloud Run...")
run(f"""gcloud run deploy {SERVICE} \
  --image={IMAGE} \
  --platform=managed \
  --region={REGION} \
  --allow-unauthenticated \
  --add-cloudsql-instances={INSTANCE} \
  --set-secrets=DB_PASSWORD=db-password:latest,DB_USER=db-user:latest,DB_HOST=db-host:latest,DB_NAME=db-name:latest,JWT_SECRET=jwt-secret:latest,GEMINI_API_KEY=gemini-api-key:latest,SCHEDULER_SECRET=scheduler-secret:latest,EVOLUTION_API_KEY=evolution-api-key:latest \
  --set-env-vars=ENVIRONMENT=production,EVOLUTION_URL=https://evolution-api-jwhcoybcga-rj.a.run.app,EVOLUTION_INSTANCE=prazu-bot \
  --memory=512Mi \
  --cpu=1 \
  --min-instances=0 \
  --max-instances=10 \
  --project={PROJECT}""")

print("\n→ Buscando URL do serviço...")
result = subprocess.run(
    f"gcloud run services describe {SERVICE} --region={REGION} --project={PROJECT} --format='value(status.url)'",
    shell=True, capture_output=True, text=True
)
url = result.stdout.strip()
print(f"\n{'=' * 60}")
print(f"✅ DEPLOY CONCLUÍDO!")
print(f"🌐 URL: {url}")
print(f"{'=' * 60}")
print(f"\nGuarda essa URL — precisamos dela para configurar o webhook.")
