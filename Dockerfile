# =============================================================================
# Dockerfile — Prazu Fase 2
# Cloud Run (southamerica-east1)
# =============================================================================

FROM python:3.11-slim

# Evita prompts interativos durante apt
ENV DEBIAN_FRONTEND=noninteractive
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

WORKDIR /app

# Dependências do sistema (psycopg2 precisa de libpq)
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq-dev \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Instala dependências Python
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copia o projeto inteiro
COPY . .

# cal_forense/calendar_v2.db vai junto — somente leitura em produção
# Garante que o arquivo existe (falha no build se não estiver)
RUN test -f cal_forense/calendar_v2.db || (echo "ERRO: calendar_v2.db não encontrado" && exit 1)

# Porta padrão Cloud Run
EXPOSE 8080

# Inicia o servidor
# Cloud Run injeta a variável PORT automaticamente
CMD ["sh", "-c", "uvicorn web.app:app --host 0.0.0.0 --port ${PORT:-8080} --workers 1"]
