# PrazorBot Brasil — Project Knowledge

## 1. O QUE É

PrazorBot Brasil é um bot Telegram que monitora prazos processuais para advogados brasileiros. É o MVP do Prazor, um SaaS legaltech com visão de se tornar o copiloto jurídico nacional.

**Repo:** https://github.com/cerosplataforms/prazorbot-brasil.git (privado)
**Stack:** Python 3.11+, SQLite, python-telegram-bot, APScheduler, Groq (Llama 3.3 70B)
**Status:** Em produção local (Mac), com usuário(s) real(is)
**Versão atual:** v3.4

---

## 2. ARQUITETURA

```
prazorbot-brasil/
├── bot.py                  # Orquestrador Telegram: comandos, jornada cadastro, handlers
├── djen.py                 # API REST DJEN + verificação DataJud + MOVS_MANIFESTACAO
├── ia.py                   # Integração Groq (Llama 3.3 70B) para briefing e perguntas
├── prazos_calc.py          # Motor de cálculo: CPC arts. 216, 219, 220, 224
├── database.py             # SQLite: advogados, processos, publicações, prazos
├── datajud.py              # Consulta API pública DataJud para detalhes de processos
├── scheduler.py            # Briefing automático diário + monitoramento DJEN (APScheduler)
├── requirements.txt
├── .env                    # TELEGRAM_TOKEN, GROQ_API_KEY
└── cal_forense/
    ├── __init__.py
    ├── calendar_v2.db      # Banco calendário forense (schema v2 normalizado)
    ├── calendar_store.py   # CRUD do banco de calendário
    ├── calendar_resolver.py # Resolução: dado processo+comarca, quais feriados se aplicam
    └── calendar_loader.py  # Carrega/popula o banco com dados de feriados
```

---

## 3. SCHEMA DO BANCO DE CALENDÁRIO (calendar_v2.db)

### tribunais
```sql
CREATE TABLE tribunais (
    id TEXT PRIMARY KEY,              -- 'TJMG', 'TRF6', 'TRT1', 'STF'
    nome TEXT NOT NULL,
    sigla TEXT NOT NULL,
    justica TEXT NOT NULL,            -- 'estadual'|'federal'|'trabalho'|'militar'|'eleitoral'|'superior'
    instancia TEXT NOT NULL,          -- '1e2grau'|'superior'|'supremo'
    uf TEXT,
    segmento_cnj TEXT,               -- '8' (estadual), '4' (federal), '5' (trabalho)
    codigo_cnj TEXT,
    regimento_feriados TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
-- 63 tribunais cadastrados
```

### localidades
```sql
CREATE TABLE localidades (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    tribunal_id TEXT NOT NULL REFERENCES tribunais(id),
    nome TEXT NOT NULL,
    tipo TEXT NOT NULL,               -- 'comarca'|'subsecao'|'vara'|'forum'
    uf TEXT NOT NULL,
    municipio_ibge TEXT,
    sede_tribunal BOOLEAN DEFAULT 0,
    ativo BOOLEAN DEFAULT 1,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(tribunal_id, nome)
);
-- 1.971 localidades cadastradas
```

### eventos
```sql
CREATE TABLE eventos (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    data DATE NOT NULL,
    ano INTEGER NOT NULL,
    data_fim DATE,                    -- NULL se dia único, preenchido se período
    descricao TEXT NOT NULL,
    tipo TEXT NOT NULL,               -- 'feriado_nacional'|'feriado_estadual'|'feriado_forense'|'feriado_municipal'|'recesso'|'ponto_facultativo'|'suspensao'
    subtipo TEXT,
    abrangencia TEXT NOT NULL,        -- 'nacional'|'estadual'|'tribunal'|'municipal'
    uf TEXT,
    tribunal_id TEXT REFERENCES tribunais(id),
    localidade_id INTEGER REFERENCES localidades(id),
    suspende_prazo BOOLEAN NOT NULL DEFAULT 1,
    suspende_expediente BOOLEAN NOT NULL DEFAULT 1,
    suspende_eletronico BOOLEAN NOT NULL DEFAULT 1,
    meio_expediente BOOLEAN NOT NULL DEFAULT 0,
    observacao TEXT,
    fonte TEXT,
    lei_base TEXT,
    confianca TEXT DEFAULT 'high',
    hash TEXT UNIQUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
-- 5.444 eventos cadastrados
```

---

## 4. REGRAS DE CÁLCULO DE PRAZO (CPC)

- **Art. 216:** Feriados da comarca DO PROCESSO (não do advogado)
- **Art. 219:** Contagem em dias úteis (exclui fds, feriados, recesso)
- **Art. 220:** Recesso forense: 20/dez a 20/jan
- **Art. 224:** Exclui dia do começo, inclui dia do vencimento
- Publicação DJEN = 1º dia útil após disponibilização
- Início prazo = 1º dia útil após publicação

---

## 5. APIs UTILIZADAS

### DJEN (Diário da Justiça Eletrônico Nacional)
- Endpoint: `https://comunicaapi.pje.jus.br/api/v1/comunicacao`
- GET com parâmetros OAB + paginação, sem autenticação

### DataJud (CNJ)
- Endpoint: `https://api-publica.datajud.cnj.jus.br/api_publica_{tribunal}/_search`
- API Key pública do CNJ

### Groq (IA)
- Modelo: Llama 3.3 70B Versatile
- Uso: briefing diário e respostas sobre processos
- Fallback: Google Gemini

---

## 6. COMANDOS DO BOT

| Comando | Descrição |
|---------|-----------|
| /start | Cadastro + importação automática de processos via DJEN |
| /briefing | Briefing IA: prazos hoje, vencidos, próximos 7d, em aberto, cumpridos |
| /djen | Publicações DJEN (30 dias) com prazos calculados + verificação DataJud |
| /calcular | Cálculo manual de prazo com feriados da comarca |
| /meus_processos | Lista processos monitorados |
| /buscar | Nova busca DJEN para importar processos |
| /adicionar | Cadastro manual de processo por número CNJ |
| /feriados | Lista feriados da comarca |
| /comarca | Altera comarca padrão |
| /publicacoes | Ver publicações DJEN salvas |
| /config | Ver configurações do usuário |
| /ajuda | Lista de comandos |

---

## 7. FUNCIONALIDADES v3.4

- Importação automática de processos pela OAB via DJEN (API REST)
- Cálculo de prazos com feriados municipais, estaduais e recesso forense
- Verificação de cumprimento via DataJud (juntada de petição)
- Briefing diário com IA (Groq/Llama 3.3 70B)
- Status inteligente: ✅ cumprido, 🟢 em aberto, 🟡 próximo, 🔴 decurso, ⚠️ verificar
- Comarca automática pelo número CNJ do processo
- Notificações de prazo urgente a cada 3h (3 dias, 1 dia, hoje)
- Monitoramento DJEN agendado (diário 11h BRT, busca a cada 5 dias por usuário)

---

## 8. VISÃO DE NEGÓCIO — ROADMAP 3 ANOS

### Mercado
- 84 milhões de processos ativos (CNJ 2024)
- ~1,4 milhão de advogados com OAB ativa
- Legaltechs brasileiras em crescimento, ninguém dominou o relacionamento diário

### Ano 1 — "O despertador do advogado"
- Entra pela dor mais aguda: prazo
- Briefing matinal via WhatsApp/Telegram que vira hábito
- Meta: 10 mil advogados ativos, retenção >85%

### Ano 2 — "O cérebro da operação"
- Copiloto de inteligência: relatórios de carteira, processos parados, jurisprudência, peças simples
- **B2B para escritórios** que pagam pra equipe inteira ter o benefício
- Meta: 50 mil advogados, plano escritório rodando

### Ano 3 — "A plataforma onde o advogado vive"
- Analytics preditivo por vara/juiz
- Marketplace de correspondentes jurídicos
- B2B enterprise (bancos, telecom, varejo)
- Expansão lusófona (Portugal, Angola, Moçambique)
- Meta: 200 mil+ advogados, Série A

### Moat (fosso competitivo)
Não é o scraping nem a IA — é o **hábito**. Advogado que abre a mensagem todo dia às 7h por 6 meses não troca. Cada dia de uso acumula dados que alimentam inteligência exclusiva.

### Naming
- Nome escolhido: **Prazor** (prazo + or = aquele que faz)
- Se a visão escalar, pode virar marca-mãe + módulo (tipo Nu → Nubank)
- Alternativas discutidas: Égide, Vigília, Lexor, Vallor

---

## 9. DEPLOY ATUAL

- Roda localmente no Mac (produção local)
- Python 3.11+ com venv
- .env com TELEGRAM_TOKEN e GROQ_API_KEY
- Banco calendar_v2.db pré-populado no repo

---

## 10. BUGS CONHECIDOS/CORRIGIDOS (v3.0→v3.4)

- DJEN Selenium substituído por API REST (sem Chrome/WebDriver)
- MOVS_MANIFESTACAO sem acentos corrigido
- calendar.db vazio no deploy → pré-populado
- Path calendar.db corrigido
- Variável comarca indefinida no calendar_resolver.py
- Função _send_msg ausente no bot.py
- ia.py com API key hardcoded → env var
- Briefing sem prazos DJEN → consulta DJEN ao vivo antes de gerar

---

## 11. COBERTURA DO CALENDÁRIO FORENSE

### Dados atuais (calendar_v2.db) — mar/2026:
- 63+ tribunais
- 2.100+ localidades
- ~6.120 eventos 2026

**Documento completo:** `.planning/COBERTURA_CALENDARIO.md`

### Resumo por status (atualizado 2026-03-07)

| Status | UFs |
|--------|-----|
| **Completo** (17) | AC, AP, BA, DF, ES, GO, MG, MS, **PE** (97 comarcas), PR, RJ, RS, SC, SE, SP |
| **Expandido** (9) | CE, MA, PA, PB, PI, RN, TO, AL (+ TJDFT) |
| **Parcial** (3) | MT, RO, RR |
| **Incompleto** (1) | AM |

### Expansões recentes (commits mar/2026)
- TJPE: 97 comarcas, 303 eventos
- TJCE: 48 comarcas | TJMA: 35 | TJPA: 38 | TJPI: 30 | TJPB: 34 | TJRN: 37 | TJTO: 21
- TJDFT: 16 circunscrições (Portaria 105/2025)

### Tabela por UF (localidades no DB)

| UF | Loc | UF | Loc | UF | Loc |
|----|-----|-----|-----|-----|-----|
| AC | 22 | AL | 10 | AM | 4 |
| AP | 13 | BA | 224 | CE | 28 |
| DF | 1 | ES | 70 | GO | 128 |
| MA | 17 | MG | 389 | MS | 76 |
| MT | 80 | PA | 21 | PB | 16 |
| PE | 97 | PI | 19 | PR | 168 |
| RJ | 86 | RN | 20 | RO | 34 |
| RR | 10 | RS | 170 | SC | 113 |
| SE | 51 | SP | 340 | TO | 14 |

---

## 12. CONVENÇÕES DE CÓDIGO

- Tudo em Python, sem frameworks web (bot direto via python-telegram-bot)
- SQLite para ambos os bancos (operacional e calendário)
- APScheduler para jobs periódicos
- Logs via logging padrão
- Chaves sensíveis em .env (nunca hardcoded)
- Dedup de eventos via campo hash na tabela eventos
