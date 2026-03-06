# PrazorBot Brasil 🇧🇷⚖️

Bot Telegram para advogados brasileiros. Calcula prazos processuais com feriados por comarca, busca processos via DJEN + DataJud do CNJ, e gera briefings diários com IA.

## Cobertura

- **27 UFs** + Distrito Federal
- **97 comarcas** com feriados municipais
- **4 cenários** de início de contagem (CPC art. 231)
- **Todos os tribunais** estaduais, federais, trabalhistas e eleitorais

## Módulos

| Arquivo | Linhas | Função |
|---------|--------|--------|
| `bot.py` | ~1080 | Bot Telegram — onboarding, comandos, IA |
| `database.py` | ~370 | SQLite — advogados, processos, prazos, feriados |
| `prazos_calc.py` | ~260 | Motor de prazos CPC-compliant |
| `feriados_br.py` | ~780 | 97 comarcas, 27 UFs, suspensões forenses |
| `djen.py` | ~560 | API REST DJEN + DataJud (verificação de prazos) |
| `datajud.py` | ~90 | API pública DataJud CNJ (busca por número CNJ) |
| `ia.py` | ~130 | Briefing e perguntas via Groq (Llama) |
| `test_prazobot.py` | ~780 | 144 testes automatizados |

## Stack

- **Busca de processos**: DJEN API REST (`comunicaapi.pje.jus.br`) + DataJud CNJ
- **Feriados**: Base hardcoded por UF/comarca (sem dependência de API externa)
- **IA**: Groq API (Llama 3.1 70B) — briefings e perguntas em linguagem natural
- **Bot**: python-telegram-bot v20+
- **Banco**: SQLite (local, sem servidor)

## Instalação

```bash
git clone <repo>
cd prazorbot-brasil
python -m venv venv
source venv/bin/activate
pip install python-telegram-bot python-dotenv requests groq
```

## Configuração

Crie `.env`:

```env
TELEGRAM_TOKEN=seu_token_do_botfather
GROQ_API_KEY=sua_chave_groq
```

A chave do DataJud já está embutida (API pública do CNJ).

## Uso

```bash
python bot.py
```

### Comandos do Bot

| Comando | Função |
|---------|--------|
| `/start` | Cadastro: nome → OAB/UF → comarca |
| `/buscar` | Busca processos via DJEN + DataJud |
| `/meus_processos` | Lista processos monitorados |
| `/calcular DD/MM/AAAA DIAS` | Calcula prazo com feriados |
| `/prazo` | Buscar por cliente ou adicionar prazo |
| `/djen` | Consultar publicações DJEN com prazos |
| `/feriados` | Lista feriados da comarca |
| `/comarca` | Alterar UF/comarca |
| `/briefing` | Gerar briefing com IA |
| `/config` | Horário do briefing automático |
| `/ajuda` | Todos os comandos |

### Cenários de Contagem (CPC art. 231)

O motor suporta 5 tipos de ciência:

| Tipo | Descrição | Início |
|------|-----------|--------|
| `djen` | Publicação no Diário Eletrônico | 1º útil após publicação |
| `ciencia_expressa` | Advogado abriu no PJe | 1º útil após leitura |
| `ciencia_tacita` | Não abriu em 10 dias (PJe) | 1º útil após 10º dia |
| `dje_consultada` | Citação via DJE — consultada | 5º dia útil após consulta |
| `dje_tacita` | Citação via DJE — não consultada | 1º útil após 10º dia |

### Comarcas por Estado

| UF | Comarcas | UF | Comarcas |
|----|----------|----|----------|
| MG | 24 | SP | 9 |
| RJ | 8 | BA | 6 |
| PR | 6 | PE | 5 |
| RS | 5 | CE | 4 |
| SC | 4 | PA | 4 |
| ES | 4 | GO | 3 |
| Demais 15 UFs | 1 cada (capital) | | |

## Testes

```bash
python test_prazobot.py
```

144 testes em 12 seções:
1. Database — carga de feriados
2. Funções auxiliares — recesso e dia útil
3. Publicação e início de prazo
4. Prazos em dias úteis
5. Prazos em dias corridos
6. Cálculo completo (disponibilização → vencimento)
7. Diferença entre comarcas MG
8. Database — advogados, processos, prazos
9. Edge cases
10. Validação cruzada — casos reais
11. Cenários de início de contagem (CPC art. 231)
12. Expansão nacional — testes multi-estado (SP, RJ, BA, RS, PE, CE, PR, SC, PA, GO, ES, DF)

## Fluxo de Busca de Processos

```
Advogado informa OAB/UF
        │
        ▼
  DJEN API REST (comunicaapi.pje.jus.br)
  → Retorna publicações dos últimos 90 dias
  → Extrai números CNJ únicos
        │
        ▼
  DataJud API (api-publica.datajud.cnj.jus.br)
  → Para cada CNJ: classe, órgão, assuntos, movimentações
        │
        ▼
  SQLite: salva processo com tribunal inferido pelo CNJ
        │
        ▼
  Motor de Prazos: calcula vencimentos com feriados da comarca
```

## Licença

Uso privado. PrazorBot © 2026.
