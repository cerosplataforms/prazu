# Prazor — Documentação Completa (para leigos e desenvolvedores)

Este documento explica **o que é o projeto**, **o que cada arquivo faz** (em linguagem simples) e **o fluxo completo** do que acontece quando alguém usa o bot. Serve tanto para quem não programa quanto para quem vai dar manutenção no código.

---

## 1. O que é o Prazor?

O **Prazor** (ou PrazorBot) é um **bot do Telegram** que ajuda advogados a **não perder prazos processuais**. Ele:

- **Busca processos** do advogado pela OAB (número da Ordem dos Advogados) em um sistema público (DJEN).
- **Calcula prazos** considerando feriados e recesso da Justiça **por comarca** (cidade onde o processo tramita), conforme o Código de Processo Civil.
- **Envia um resumo diário** (briefing) com prazos que vencem hoje, vencidos, próximos e em aberto.
- **Verifica** se um prazo foi cumprido consultando o DataJud (sistema do CNJ).

Ou seja: o advogado conversa com o bot no Telegram, cadastra OAB e comarca, e passa a receber lembretes e cálculos de prazo com base nos feriados da comarca de cada processo.

**Cobertura do calendário (mar/2026):** 17 UFs completas + DF, 9 UFs expandidas (CE, MA, PA, PI, PB, RN, TO, AL e TJDFT), PE com 97 comarcas, ~6.120 eventos no ano. Detalhes em `.planning/COBERTURA_CALENDARIO.md`.

---

## 2. Resultado dos testes (março/2026)

Os testes automatizados foram executados com sucesso:

- **129 testes passando**, 0 falhando.
- Comando para rodar: `python3 test_prazobot.py`

Os testes cobrem:

1. Carga de feriados no banco e listagem de comarcas.
2. Recesso forense e “dia útil” (fim de semana, feriado, recesso).
3. Cálculo de data de publicação e de início do prazo.
4. Prazos em dias úteis e em dias corridos.
5. Fluxo completo: disponibilização → publicação → início → vencimento.
6. Diferença entre comarcas (feriados diferentes).
7. Cadastro de advogados, processos e prazos no banco.
8. Casos extremos (prazo 0, 1 dia, 360 dias, etc.).
9. Casos reais (contestação, recurso em dobro, Carnaval, recesso).
10. Cenários de contagem (hoje só cenário DJEN).
11. Expansão nacional (várias UFs e comarcas).

---

## 3. Fluxo geral (do usuário até a resposta)

Resumo em etapas:

1. **Usuário abre o bot no Telegram** e manda `/start`.
2. **bot.py** recebe o comando. Se for usuário novo, inicia o cadastro (nome → OAB → horário do lembrete → comarca). Se já for cadastrado, mostra um menu rápido.
3. **database.py** guarda ou lê os dados do advogado no arquivo **prazobot.db** (SQLite).
4. Se o usuário pedir **buscar processos** (`/buscar` ou durante o cadastro):
   - **djen.py** chama a API do DJEN (Diário da Justiça Eletrônico) com o número da OAB e busca as publicações.
   - **datajud.py** é usada para enriquecer cada processo (classe, assuntos, movimentações) via API pública do DataJud (CNJ).
   - Os processos e prazos são salvos no **prazobot.db**; o cálculo de vencimento usa **prazos_calc.py** e o calendário forense.
5. **Cálculo de prazos** (comando `/calcular` ou ao importar publicações):
   - **prazos_calc.py** usa as regras do CPC (publicação no 1º dia útil, início no 1º dia útil após a publicação, contagem em dias úteis, recesso 20/dez–20/jan).
   - **cal_forense** (calendar_resolver + calendar_store) diz quais dias são “úteis” para uma UF e comarca (considerando feriados nacionais, estaduais, municipais e recesso).
   - O banco **cal_forense/calendar_v2.db** contém tribunais, localidades e eventos (feriados/suspensões).
6. **Briefing diário** (comando `/briefing` ou envio automático):
   - **scheduler.py** (quando rodado como cron) ou **bot.py** chama **ia.py**.
   - **ia.py** usa a API da Groq (modelo Llama) para gerar um texto em linguagem natural a partir da lista de processos e prazos que vêm do **database** e do **prazos_calc**.
   - O bot envia essa mensagem no Telegram.
7. **Atualização noturna** (opcional, via cron):
   - **atualizar.py** percorre os processos do banco e chama **datajud.py** para atualizar movimentações e verificar cumprimento de prazos.

Ou seja: **bot.py** é a “porta de entrada”; **database.py** e **prazobot.db** guardam usuários e processos; **djen.py** e **datajud.py** buscam dados externos; **prazos_calc.py** e **cal_forense** calculam prazos; **ia.py** gera o texto do briefing; **scheduler.py** e **atualizar.py** rodam tarefas periódicas.

---

## 4. O que cada arquivo faz (explicação para leigos)

### Na raiz do projeto

| Arquivo | O que faz (em poucas palavras) |
|--------|---------------------------------|
| **bot.py** | Programa principal do bot no Telegram: recebe mensagens, comandos e botões, faz o cadastro (nome, OAB, horário, comarca), chama busca de processos, cálculo de prazos, briefing e listagens. É o “cérebro” que orquestra tudo que o usuário vê. |
| **database.py** | Acesso ao banco de dados **prazobot.db**: cria e atualiza tabelas de advogados, processos, prazos, andamentos, feriados (legado) e comunicações do DJEN. Todas as leituras/gravações de usuário e processo passam por aqui. |
| **prazos_calc.py** | Motor de cálculo de prazos: a partir da data de disponibilização (e UF/comarca), calcula data de publicação, início do prazo e vencimento em dias úteis ou corridos, respeitando CPC (recesso, 1º dia útil, etc.). Usa o **cal_forense** para saber o que é dia útil. |
| **djen.py** | Consulta a API do **DJEN** (Diário da Justiça Eletrônico): busca publicações pelo número da OAB, trata a resposta, importa processos e prazos para o banco e pode verificar se um prazo foi cumprido (com ajuda do DataJud). |
| **datajud.py** | Consulta a **API pública do DataJud (CNJ)** para obter detalhes do processo (classe, órgão, movimentações, etc.) e atualizar o banco. Usado na busca de processos e no script de atualização noturna. |
| **ia.py** | Integração com **Groq (Llama)** para gerar o texto do briefing e responder perguntas em linguagem natural usando a lista de processos e prazos que o sistema já calculou. |
| **scheduler.py** | Script que pode ser agendado (cron): a cada execução, verifica o horário configurado de cada advogado e envia o briefing na hora certa via Telegram. |
| **atualizar.py** | Script para rodar de madrugada (cron): atualiza todos os processos cadastrados no DataJud e reflete no banco (movimentações, cumprimento de prazos). |
| **feriados_br.py** | Listas e funções de feriados nacionais, estaduais e municipais para **várias comarcas**; usado para popular a tabela de feriados do **prazobot.db** (legado) e em parte dos testes. O cálculo “de produção” usa o **cal_forense** e o **calendar_v2.db**. |
| **feriados_mg.py** | Módulo legado com feriados de Minas Gerais; pode ser usado como fallback ou em testes. |
| **test_prazobot.py** | Suite de testes: cria um banco de teste, carrega feriados, testa recesso, dia útil, publicação, início, prazos em dias úteis/corridos, cálculo completo, comarcas, banco de advogados/processos, casos reais e vários estados. Rodar: `python3 test_prazobot.py`. |

### Pasta cal_forense (calendário forense)

| Arquivo | O que faz (em poucas palavras) |
|--------|---------------------------------|
| **calendar_store.py** | Lê e escreve no banco **calendar_v2.db** (tribunais, localidades, eventos). Fornece listas de feriados/eventos por ano, UF e comarca. Suporta schema antigo (v1) e novo (v2). |
| **calendar_resolver.py** | Responde: “esta data é dia útil forense?” para uma UF e comarca. Considera fim de semana, recesso (20/dez–20/jan), feriados e suspensões do banco. É o que o **prazos_calc** usa para contar dias úteis. |
| **calendar_loader.py** | Script que **popula** o **calendar_v2.db**: insere tribunais, localidades e eventos (feriados nacionais, estaduais, municipais, recesso, suspensões) a partir de listas no próprio código. Pode ser rodado para atualizar o banco antes de subir o bot. |
| **calendar_v2.db** | Banco SQLite com tribunais, comarcas e eventos (feriados, recesso, suspensões). É a fonte da verdade para “dia útil” no cálculo de prazos em produção. |

### Outros arquivos úteis

| Arquivo | O que faz |
|--------|-----------|
| **requirements.txt** | Lista de dependências Python (telegram, requests, groq, etc.). |
| **.env** | Variáveis de ambiente (token do Telegram, chave da Groq). Não deve ser commitado. |
| **.env.example** | Exemplo do que colocar no `.env`. |
| **README.md** | Visão geral do projeto, instalação, comandos do bot e testes. |
| **.planning/** | Documentos de planejamento (ROADMAP, fases, cobertura do calendário, etc.). |

---

## 5. Fluxo detalhado por comando

### /start (primeira vez)

1. Usuário manda `/start`.
2. **bot.py** vê que não existe advogado com aquele `chat_id` no **database**.
3. Bot pede o nome e guarda em `context.user_data`.
4. Bot pede OAB (ex.: `12345/MG`), valida e guarda.
5. Bot mostra botões de horário (6h–22h) para o lembrete diário.
6. Usuário escolhe; bot pergunta se quer lembrete no fim de semana.
7. Usuário responde; **database** cria o advogado no **prazobot.db**.
8. **djen.py** é chamado para buscar publicações pela OAB; **datajud.py** enriquece processos; **prazos_calc** + **cal_forense** calculam vencimentos; tudo é salvo no banco.
9. Bot envia mensagem de boas-vindas e sugere comarca (e comandos como `/briefing`, `/calcular`).

### /start (já cadastrado)

1. **bot.py** busca o advogado no **database** pelo `chat_id`.
2. Mostra resumo: nome, OAB, quantidade de processos, horário do lembrete e atalhos (/briefing, /buscar, /calcular, /config, /ajuda).

### /buscar

1. **bot.py** lê OAB do advogado no **database**.
2. Chama **djen.py** para buscar publicações na API do DJEN.
3. Para cada processo (número CNJ), **datajud.py** busca detalhes na API do DataJud.
4. **bot.py** + **prazos_calc** + **cal_forense** calculam publicação, início e vencimento por comarca; resultados são salvos no **database** (processos, prazos, comunicações DJEN).
5. Bot responde com resumo do que foi importado e prazos calculados.

### /calcular

1. Usuário envia algo como “05/03/2026 15” (data e número de dias).
2. **bot.py** parseia a mensagem e obtém UF/comarca do advogado (ou do processo).
3. **prazos_calc.calcular_prazo_completo** calcula publicação, início e vencimento usando **cal_forense** para dias úteis.
4. Bot devolve as datas formatadas.

### /briefing

1. **bot.py** chama **database** para listar processos do advogado com prazos (e andamentos).
2. Para cada prazo, o status (hoje, vencido, próximo, em aberto, cumprido) já vem do banco/cálculo.
3. **ia.py** recebe essa lista e gera um texto (resumo) com a API Groq.
4. **bot.py** envia esse texto no Telegram.

### /djen

1. **bot.py** chama **djen.py** para buscar publicações recentes pela OAB.
2. **djen** pode cruzar com **datajud** para marcar prazos cumpridos.
3. **bot** formata e envia a lista de publicações com prazos calculados.

### Lembrete automático (scheduler)

1. **scheduler.py** é executado (ex.: a cada hora via cron).
2. Lê no **database** todos os advogados ativos e o horário de briefing de cada um.
3. Para quem está no horário atual, chama **database** (processos + prazos) e **ia.py** (briefing).
4. Envia a mensagem pelo Telegram com o token do bot.

---

## 6. Bancos de dados (resumo)

- **prazobot.db** (raiz): advogados, processos, prazos, andamentos, feriados (legado), comunicações DJEN. Usado pelo **bot** e pelos scripts.
- **cal_forense/calendar_v2.db**: tribunais, localidades, eventos (feriados, recesso, suspensões). Usado por **calendar_store** e **calendar_resolver** no cálculo de “dia útil”.
- **prazobot_test.db**: criado e apagado pelos testes (**test_prazobot.py**).

---

## 7. Como rodar (resumo)

- **Bot**: `python3 bot.py` (precisa de `.env` com `TELEGRAM_TOKEN` e `GROQ_API_KEY`).
- **Testes**: `python3 test_prazobot.py`.
- **Briefing manual (todos no horário)**: `python3 scheduler.py --force`.
- **Atualização noturna**: `python3 atualizar.py` (pode ser agendado no cron).
- **Popular calendário**: `python3 cal_forense/calendar_loader.py` (conforme uso documentado no próprio script).

---

## 8. Resumo em uma frase por arquivo

- **bot.py** — Recebe e responde no Telegram; cadastra usuário e orquestra comandos.
- **database.py** — Lê e grava advogados, processos e prazos no prazobot.db.
- **prazos_calc.py** — Calcula data de publicação, início e vencimento de prazos (CPC).
- **djen.py** — Busca publicações no DJEN pela OAB e importa processos/prazos.
- **datajud.py** — Busca detalhes do processo no DataJud (CNJ).
- **ia.py** — Gera o texto do briefing e respostas em linguagem natural (Groq).
- **scheduler.py** — Envia o briefing no horário configurado (cron).
- **atualizar.py** — Atualiza processos no DataJud (cron noturno).
- **feriados_br.py** — Listas de feriados por comarca (legado + testes).
- **cal_forense/calendar_store.py** — Acesso ao calendar_v2.db (eventos por UF/comarca).
- **cal_forense/calendar_resolver.py** — Diz se uma data é dia útil forense.
- **cal_forense/calendar_loader.py** — Popula o calendar_v2.db.
- **test_prazobot.py** — Testes automatizados (129 casos).

---

*Documentação atualizada em março/2026. Testes: 129 passando. Cobertura: 17 UFs completas + 9 expandidas (CE, MA, PA, PI, PB, RN, TO, AL, TJDFT); PE 97 comarcas; ~6.120 eventos 2026.*
