-- =============================================================================
-- migrate_fase2.sql — Prazu Fase 2
-- Schema Postgres para Cloud SQL (prazu-prod / prazu-db / database: prazu)
--
-- Execução:
--   Via Cloud Shell:
--   gcloud sql connect prazu-db --user=prazu_user --database=prazu
--   \i migrate_fase2.sql
--
--   Ou via psql direto:
--   psql "host=34.39.197.67 dbname=prazu user=prazu_user password=Prazu@2026!" -f migrate_fase2.sql
-- =============================================================================

-- Extensões úteis
CREATE EXTENSION IF NOT EXISTS "pgcrypto";  -- gen_random_uuid()

-- =============================================================================
-- ADVOGADOS
-- Tabela central. chat_id mantido pra compatibilidade com bot.py legado.
-- Novos campos Fase 2: email, senha_hash, whatsapp, status, trial, stripe.
-- =============================================================================
CREATE TABLE IF NOT EXISTS advogados (
    id                      SERIAL PRIMARY KEY,
    -- Telegram (legado, nullable pra novos cadastros via site)
    chat_id                 BIGINT UNIQUE,
    -- Dados pessoais
    nome                    TEXT NOT NULL,
    email                   TEXT UNIQUE,
    senha_hash              TEXT,
    -- OAB
    oab_numero              TEXT NOT NULL,
    oab_seccional           TEXT NOT NULL,
    -- Localização
    comarca                 TEXT DEFAULT '',
    -- Configurações bot
    horario_briefing        TEXT DEFAULT '07:00',
    lembrete_fds            BOOLEAN DEFAULT FALSE,
    ultima_busca_djen       TIMESTAMPTZ,
    ativo                   BOOLEAN DEFAULT TRUE,
    -- WhatsApp
    whatsapp                TEXT UNIQUE,
    zapi_confirmado         BOOLEAN DEFAULT FALSE,
    -- Assinatura
    status                  TEXT DEFAULT 'trial'
                            CHECK (status IN ('trial','ativo','expirado','cancelado')),
    trial_inicio            TIMESTAMPTZ,
    trial_fim               TIMESTAMPTZ,
    -- Stripe
    stripe_customer_id      TEXT UNIQUE,
    stripe_subscription_id  TEXT UNIQUE,
    -- Controle
    criado_em               TIMESTAMPTZ DEFAULT NOW(),
    last_seen               TIMESTAMPTZ,
    UNIQUE (oab_numero, oab_seccional)
);

-- =============================================================================
-- PROCESSOS
-- =============================================================================
CREATE TABLE IF NOT EXISTS processos (
    id              SERIAL PRIMARY KEY,
    advogado_id     INTEGER NOT NULL REFERENCES advogados(id) ON DELETE CASCADE,
    numero          TEXT NOT NULL,
    partes          TEXT,
    vara            TEXT,
    tribunal        TEXT DEFAULT 'TJMG',
    comarca         TEXT,
    materia         TEXT,
    classe          TEXT,
    assunto         TEXT,
    status          TEXT DEFAULT 'ativo' CHECK (status IN ('ativo','arquivado','encerrado')),
    fonte           TEXT DEFAULT 'manual' CHECK (fonte IN ('manual','djen','datajud')),
    criado_em       TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE (advogado_id, numero)
);

-- =============================================================================
-- PRAZOS
-- =============================================================================
CREATE TABLE IF NOT EXISTS prazos (
    id                  SERIAL PRIMARY KEY,
    processo_id         INTEGER NOT NULL REFERENCES processos(id) ON DELETE CASCADE,
    tipo                TEXT NOT NULL,
    data_inicio         DATE,
    data_fim            DATE NOT NULL,
    data_fim_util       DATE,
    dias_totais         INTEGER,
    contagem            TEXT DEFAULT 'uteis' CHECK (contagem IN ('uteis','corridos')),
    fatal               BOOLEAN DEFAULT FALSE,
    cumprido            BOOLEAN DEFAULT FALSE,
    notificado          BOOLEAN DEFAULT FALSE,
    notificado_3d       BOOLEAN DEFAULT FALSE,
    notificado_1d       BOOLEAN DEFAULT FALSE,
    notificado_hoje     BOOLEAN DEFAULT FALSE,
    criado_em           TIMESTAMPTZ DEFAULT NOW()
);

-- =============================================================================
-- ANDAMENTOS
-- =============================================================================
CREATE TABLE IF NOT EXISTS andamentos (
    id          SERIAL PRIMARY KEY,
    processo_id INTEGER NOT NULL REFERENCES processos(id) ON DELETE CASCADE,
    data        DATE NOT NULL,
    descricao   TEXT NOT NULL,
    notificado  BOOLEAN DEFAULT FALSE,
    criado_em   TIMESTAMPTZ DEFAULT NOW()
);

-- =============================================================================
-- COMUNICAÇÕES DJEN
-- =============================================================================
CREATE TABLE IF NOT EXISTS comunicacoes_djen (
    id                      SERIAL PRIMARY KEY,
    advogado_id             INTEGER NOT NULL REFERENCES advogados(id) ON DELETE CASCADE,
    numero_processo         TEXT,
    tribunal                TEXT,
    conteudo                TEXT,
    data_disponibilizacao   DATE,
    data_publicacao         DATE,
    tipo_comunicacao        TEXT,
    lida                    BOOLEAN DEFAULT FALSE,
    importada_em            TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE (advogado_id, numero_processo, data_disponibilizacao)
);

-- =============================================================================
-- ASSINATURAS — histórico de planos e pagamentos
-- =============================================================================
CREATE TABLE IF NOT EXISTS assinaturas (
    id                      SERIAL PRIMARY KEY,
    advogado_id             INTEGER NOT NULL REFERENCES advogados(id) ON DELETE CASCADE,
    plano                   TEXT NOT NULL DEFAULT 'individual'
                            CHECK (plano IN ('individual','escritorio','enterprise')),
    status                  TEXT NOT NULL DEFAULT 'trial'
                            CHECK (status IN ('trial','ativo','cancelado','expirado')),
    periodo_inicio          DATE,
    periodo_fim             DATE,
    stripe_subscription_id  TEXT,
    stripe_price_id         TEXT,
    valor_centavos          INTEGER,
    criado_em               TIMESTAMPTZ DEFAULT NOW(),
    atualizado_em           TIMESTAMPTZ DEFAULT NOW()
);

-- =============================================================================
-- SESSIONS — refresh tokens para autenticação do site
-- =============================================================================
CREATE TABLE IF NOT EXISTS sessions (
    id          SERIAL PRIMARY KEY,
    advogado_id INTEGER NOT NULL REFERENCES advogados(id) ON DELETE CASCADE,
    token       TEXT UNIQUE NOT NULL,
    user_agent  TEXT DEFAULT '',
    ip          TEXT DEFAULT '',
    expires_at  TIMESTAMPTZ NOT NULL,
    criado_em   TIMESTAMPTZ DEFAULT NOW()
);

-- =============================================================================
-- WHATSAPP EVENTS — log de mensagens Z-API
-- =============================================================================
CREATE TABLE IF NOT EXISTS whatsapp_events (
    id              SERIAL PRIMARY KEY,
    advogado_id     INTEGER REFERENCES advogados(id) ON DELETE SET NULL,
    direcao         TEXT NOT NULL CHECK (direcao IN ('inbound','outbound')),
    tipo            TEXT NOT NULL,
    conteudo        TEXT DEFAULT '',
    zapi_message_id TEXT DEFAULT '',
    status          TEXT DEFAULT 'enviado',
    criado_em       TIMESTAMPTZ DEFAULT NOW()
);

-- =============================================================================
-- MIGRATIONS — controle de versão do schema
-- =============================================================================
CREATE TABLE IF NOT EXISTS migrations (
    id          SERIAL PRIMARY KEY,
    nome        TEXT NOT NULL,
    aplicado_em TIMESTAMPTZ DEFAULT NOW()
);

INSERT INTO migrations (nome) VALUES ('fase2_initial_schema');

-- =============================================================================
-- ÍNDICES
-- =============================================================================

-- advogados
CREATE INDEX IF NOT EXISTS idx_adv_email        ON advogados(email);
CREATE INDEX IF NOT EXISTS idx_adv_whatsapp     ON advogados(whatsapp);
CREATE INDEX IF NOT EXISTS idx_adv_oab          ON advogados(oab_numero, oab_seccional);
CREATE INDEX IF NOT EXISTS idx_adv_chat_id      ON advogados(chat_id);
CREATE INDEX IF NOT EXISTS idx_adv_status       ON advogados(status);
CREATE INDEX IF NOT EXISTS idx_adv_trial_fim    ON advogados(trial_fim) WHERE status = 'trial';

-- processos
CREATE INDEX IF NOT EXISTS idx_proc_advogado    ON processos(advogado_id);
CREATE INDEX IF NOT EXISTS idx_proc_numero      ON processos(numero);
CREATE INDEX IF NOT EXISTS idx_proc_status      ON processos(status);

-- prazos
CREATE INDEX IF NOT EXISTS idx_prazos_processo  ON prazos(processo_id);
CREATE INDEX IF NOT EXISTS idx_prazos_data_fim  ON prazos(data_fim) WHERE cumprido = FALSE;
CREATE INDEX IF NOT EXISTS idx_prazos_urgentes  ON prazos(data_fim) WHERE cumprido = FALSE AND fatal = TRUE;

-- comunicações
CREATE INDEX IF NOT EXISTS idx_djen_advogado    ON comunicacoes_djen(advogado_id);
CREATE INDEX IF NOT EXISTS idx_djen_processo    ON comunicacoes_djen(numero_processo);

-- sessions
CREATE INDEX IF NOT EXISTS idx_session_token    ON sessions(token);
CREATE INDEX IF NOT EXISTS idx_session_expires  ON sessions(expires_at);

-- whatsapp events
CREATE INDEX IF NOT EXISTS idx_wapp_advogado    ON whatsapp_events(advogado_id);
CREATE INDEX IF NOT EXISTS idx_wapp_criado      ON whatsapp_events(criado_em);

-- assinaturas
CREATE INDEX IF NOT EXISTS idx_assin_advogado   ON assinaturas(advogado_id);

-- =============================================================================
-- VERIFICAÇÃO FINAL
-- =============================================================================
SELECT
    schemaname,
    tablename,
    pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) AS tamanho
FROM pg_tables
WHERE schemaname = 'public'
ORDER BY tablename;
