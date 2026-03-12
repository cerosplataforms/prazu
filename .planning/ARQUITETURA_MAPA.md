# Prazu — Mapa Mental da Arquitetura

## Diagrama de componentes (Mermaid)

```mermaid
flowchart TB
    subgraph Usuarios["👤 Usuários"]
        Browser["Browser"]
        WhatsApp["WhatsApp"]
    end

    subgraph Prazu["🏗️ Prazu (Cloud Run)"]
        subgraph Web["web/"]
            App["app.py\nFastAPI"]
            Auth["auth.py\nJWT"]
            Onboarding["onboarding.py\nDJEN, Bot, Jobs"]
            Email["email_sender.py\nResend"]
            ZAPI["zapi.py\nCliente Z-API"]
        end
        
        subgraph Core["Core"]
            DB["database_gcp.py\nPostgreSQL async"]
            Prazos["prazos_calc.py\nCPC"]
            IA["ia.py\nGemini"]
        end
        
        subgraph Integracao["Integrações"]
            DJEN["djen.py"]
            DataJud["datajud.py"]
        end
        
        subgraph Dados["Dados locais"]
            Cal["cal_forense/\ncalendar_v2.db"]
        end
    end

    subgraph Servicos["☁️ Serviços externos"]
        CloudSQL["Cloud SQL\nPostgreSQL"]
        ResendSvc["Resend\nEmail"]
        ZAPISvc["Z-API\nWhatsApp"]
        GeminiSvc["Google Gemini\nIA"]
        DJENAPI["comunicaapi.pje.jus.br\nDJEN"]
        DataJudAPI["api-publica.datajud.cnj.jus.br"]
        Scheduler["Cloud Scheduler"]
    end

    Browser -->|HTTPS| App
    WhatsApp -->|Webhook| ZAPISvc
    ZAPISvc -->|POST /webhook/zapi| App
    
    App --> Auth
    App --> Onboarding
    App --> DB
    Onboarding --> ZAPI
    Onboarding --> IA
    Onboarding --> DJEN
    Onboarding --> Email
    
    ZAPI -->|send| ZAPISvc
    Email -->|API| ResendSvc
    IA -->|API| GeminiSvc
    DJEN -->|REST| DJENAPI
    DataJud -->|REST| DataJudAPI
    
    DB -->|asyncpg| CloudSQL
    Prazos --> Cal
    Onboarding --> Prazos
    Onboarding --> DataJud
    
    Scheduler -->|POST /jobs/*| App
```

---

## Mapa mental por camadas

```
Prazu
│
├── 🌐 ENTRADA
│   ├── Browser → prazu.com.br (HTTPS)
│   │   ├── /cadastro, /login, /esqueci-senha
│   │   ├── /onboarding
│   │   ├── /dashboard
│   │   ├── /configuracoes
│   │   └── /termos, /privacidade
│   │
│   ├── Webhook Z-API → /webhook/zapi
│   │   └── Mensagens WhatsApp recebidas
│   │
│   └── Cloud Scheduler → /jobs/*
│       ├── /jobs/briefing (briefing diário)
│       ├── /jobs/expirar-trials
│       ├── /jobs/djen
│       └── /jobs/lembrete-trial
│
├── 🔐 AUTENTICAÇÃO
│   ├── JWT (cookie prazu_token)
│   ├── Sessions (tabela sessions)
│   └── Dependência: advogado_logado
│
├── 💼 LÓGICA DE NEGÓCIO
│   ├── Cadastro / Login / Recuperação senha
│   ├── Onboarding (OAB, WhatsApp, preferências)
│   ├── Busca DJEN → DataJud → processos + prazos
│   ├── Cálculo de prazos (prazos_calc + cal_forense)
│   ├── Briefing (IA Gemini)
│   └── Bot WhatsApp (comandos + IA)
│
├── 🗄️ PERSISTÊNCIA
│   ├── PostgreSQL (Cloud SQL)
│   │   ├── advogados
│   │   ├── processos
│   │   ├── prazos
│   │   ├── comunicacoes_djen
│   │   └── whatsapp_events
│   └── SQLite (calendar_v2.db) — feriados forenses
│
└── 🔌 INTEGRAÇÕES
    ├── Resend → emails (códigos, recuperação senha)
    ├── Z-API → envio/recebimento WhatsApp
    ├── Gemini → briefings, respostas IA
    ├── DJEN API → publicações por OAB
    └── DataJud API → detalhes de processos (CNJ)
```

---

## Fluxo de dados simplificado

```
┌─────────────┐     ┌──────────────┐     ┌─────────────┐
│   Usuário   │────▶│  Cloud Run   │────▶│ Cloud SQL   │
│ (Web/WPP)   │     │  (FastAPI)   │     │ (PostgreSQL)│
└─────────────┘     └──────┬───────┘     └─────────────┘
                          │
          ┌───────────────┼───────────────┐
          ▼               ▼               ▼
   ┌────────────┐  ┌────────────┐  ┌────────────┐
   │ Resend     │  │ Z-API      │  │ Gemini     │
   │ (email)    │  │ (WhatsApp) │  │ (IA)       │
   └────────────┘  └────────────┘  └────────────┘
          │               │               │
          └───────────────┼───────────────┘
                          ▼
                  ┌───────────────┐
                  │ DJEN + DataJud│
                  │ (processos)   │
                  └───────────────┘
```

---

## Variáveis de ambiente por serviço

| Serviço | Variáveis principais |
|---------|----------------------|
| **App** | ENVIRONMENT, JWT_SECRET |
| **Banco** | DB_HOST, DB_NAME, DB_USER, DB_PASSWORD, CLOUD_SQL_INSTANCE |
| **Z-API** | ZAPI_INSTANCE_ID, ZAPI_TOKEN, ZAPI_CLIENT_TOKEN, ZAPI_WEBHOOK_SECRET |
| **Resend** | RESEND_API_KEY, EMAIL_FROM |
| **Gemini** | GEMINI_API_KEY |
| **Jobs** | SCHEDULER_SECRET |
