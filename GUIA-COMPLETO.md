# 🤖 PrazoBot — Guia Completo Para Iniciantes

> **⚠️ Documentação legada (bot Telegram).** O Prazu atual é app web + WhatsApp. Veja [README.md](README.md) e [SETUP.md](SETUP.md).

## Passo a passo para rodar seu bot do ZERO, mesmo sem saber programar.

---

## 📋 VISÃO GERAL — O que vamos fazer

```
1. Criar contas (5 minutos)
2. Instalar programas no seu computador (15 minutos)
3. Criar o bot no Telegram (3 minutos)
4. Baixar o código e configurar (10 minutos)
5. Rodar o bot (2 minutos)
6. Testar! (5 minutos)
```

Tempo total: ~40 minutos

---

## ETAPA 1 — Criar contas (tudo gratuito)

Você vai precisar de 3 contas. Crie todas antes de começar.

### 1.1 — Conta no GitLab (versionamento do código)

1. Acesse: **https://gitlab.com**
2. Clique em **"Register now"**
3. Preencha nome, e-mail, senha
4. Confirme o e-mail
5. Pronto! Você vai usar isso depois pra guardar seu código

### 1.2 — Conta na ZAP IA (inteligência artificial)

1. Acesse o site da ZAP IA (o site que você já tem a chave)
2. Copie e guarde em algum lugar:
   - A **chave de API** (API Key)
   - A **URL base** da API (algo como `https://api.zapia.com.br/v1`)
   - O **nome do modelo** que você pode usar (ex: `gpt-4o-mini`)
3. Se não sabe esses dados, entre no painel/dashboard da ZAP IA e procure na seção "API" ou "Configurações"

### 1.3 — Conta na Hetzner (servidor VPS) — OPCIONAL POR AGORA

Isso é pra quando quiser deixar o bot rodando 24h. Por enquanto vamos rodar no seu computador.

Se quiser criar agora pra depois:
1. Acesse: **https://www.hetzner.com/cloud**
2. Crie uma conta
3. O plano mais barato custa ~€4/mês (~R$25)

---

## ETAPA 2 — Instalar programas no seu computador

### 2.1 — Instalar o Python

O Python é a linguagem que o bot usa.

**No Windows:**
1. Acesse: **https://www.python.org/downloads/**
2. Clique no botão amarelo grande **"Download Python 3.xx"**
3. **IMPORTANTE**: Na tela de instalação, marque a caixinha:
   ☑️ **"Add Python to PATH"** (isso é muito importante!)
4. Clique em "Install Now"
5. Espere instalar

**No Mac:**
1. Abra o Terminal (Cmd + Espaço, digite "Terminal")
2. Digite: `brew install python3`
3. Se não tiver o brew, primeiro instale: acesse **https://brew.sh**

**Para verificar se instalou certo:**
1. Abra o Terminal (Windows: aperte Win+R, digite `cmd`, Enter)
2. Digite: `python --version`
3. Deve aparecer algo como: `Python 3.12.x`

### 2.2 — Instalar o VSCode

O VSCode é o editor onde você vai ver e editar o código.

1. Acesse: **https://code.visualstudio.com/**
2. Clique em **"Download"** (ele detecta seu sistema automaticamente)
3. Instale normalmente (next, next, finish)

**Depois de instalar, instale a extensão de Python:**
1. Abra o VSCode
2. Clique no ícone de quadradinhos na barra lateral esquerda (Extensions)
3. Na busca, digite: **Python**
4. Clique em **"Install"** na extensão da Microsoft (a primeira que aparece)

### 2.3 — Instalar o Git (controle de versão)

1. Acesse: **https://git-scm.com/downloads**
2. Baixe para seu sistema e instale
3. Na instalação, pode ir clicando "Next" em tudo (padrões estão ok)

---

## ETAPA 3 — Criar o Bot no Telegram

Isso é feito dentro do próprio Telegram.

1. Abra o **Telegram** no celular ou computador
2. Na busca, procure: **@BotFather**
3. Inicie uma conversa com ele
4. Envie: `/newbot`
5. Ele vai perguntar o **nome** do bot. Digite: `PrazoBot` (ou o nome que quiser)
6. Ele vai perguntar o **username**. Digite algo como: `prazobot_adv_bot`
   - Precisa terminar com `_bot`
   - Precisa ser único (se já existir, tente outro nome)
7. Ele vai te dar um **token** parecido com isso:

```
7123456789:AAHxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
```

8. **COPIE ESSE TOKEN E GUARDE!** Você vai precisar dele.

**DICA**: Envie o token pra você mesmo no Telegram pra não perder.

---

## ETAPA 4 — Baixar o código e configurar

### 4.1 — Criar a pasta do projeto

1. Abra o **VSCode**
2. Vá em **File > Open Folder** (ou Arquivo > Abrir Pasta)
3. Crie uma pasta nova chamada `prazo-bot` em um lugar fácil:
   - Windows: `C:\Users\SeuNome\prazo-bot`
   - Mac: `/Users/SeuNome/prazo-bot`
4. Selecione essa pasta e clique "Abrir"

### 4.2 — Abrir o Terminal dentro do VSCode

1. No VSCode, vá em **Terminal > New Terminal** (ou Ctrl+`)
2. Vai abrir um terminal na parte de baixo da tela
3. Verifique se está na pasta certa. Deve mostrar algo como:

```
C:\Users\SeuNome\prazo-bot>
```

### 4.3 — Baixar o código do projeto

No Terminal do VSCode, copie e cole CADA comando abaixo, um por vez, apertando Enter após cada um:

**Se você baixou o arquivo .tar.gz que eu te dei:**
1. Copie o arquivo `prazo-bot-mvp.tar.gz` para a pasta `prazo-bot`
2. No terminal:

```bash
tar -xzf prazo-bot-mvp.tar.gz --strip-components=1
```

**Se não conseguir extrair o tar, copie os arquivos manualmente:**
Você precisa desses 7 arquivos na pasta. Vou colocar o conteúdo de cada um nos passos abaixo.

### 4.4 — Criar os arquivos (se não extraiu o .tar.gz)

Se você não conseguiu extrair o arquivo, crie cada arquivo manualmente:

1. No VSCode, na barra lateral esquerda (Explorer), clique com botão direito > **New File**
2. Crie os seguintes arquivos (um por um):
   - `bot.py`
   - `ia.py`
   - `database.py`
   - `datajud.py`
   - `scheduler.py`
   - `atualizar.py`
   - `requirements.txt`
   - `.env`

Para o `requirements.txt`, o conteúdo é:

```
python-telegram-bot==21.6
openai==1.55.0
python-dotenv==1.0.1
requests==2.32.3
```

Para os outros arquivos, copie o código que eu te enviei anteriormente.

### 4.5 — Criar o arquivo .env (CONFIGURAÇÃO PRINCIPAL)

Este é o arquivo mais importante! Crie um arquivo chamado `.env` (com o ponto na frente) na pasta do projeto.

1. No VSCode, crie **New File** > digite `.env`
2. Cole o seguinte conteúdo:

```
TELEGRAM_TOKEN=COLE_SEU_TOKEN_DO_BOTFATHER_AQUI
ZAPIA_API_KEY=COLE_SUA_CHAVE_DA_ZAPIA_AQUI
ZAPIA_BASE_URL=https://api.zapia.com.br/v1
ZAPIA_MODEL=gpt-4o-mini
LOG_LEVEL=INFO
```

3. **Substitua** os valores:
   - `COLE_SEU_TOKEN_DO_BOTFATHER_AQUI` → pelo token que o BotFather te deu
   - `COLE_SUA_CHAVE_DA_ZAPIA_AQUI` → pela chave da ZAP IA
   - `ZAPIA_BASE_URL` → pela URL correta da API da ZAP IA
   - `ZAPIA_MODEL` → pelo modelo que sua chave permite

4. Salve o arquivo (Ctrl+S)

**EXEMPLO de como deve ficar:**

```
TELEGRAM_TOKEN=7123456789:AAHxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
ZAPIA_API_KEY=sk-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
ZAPIA_BASE_URL=https://api.zapia.com.br/v1
ZAPIA_MODEL=gpt-4o-mini
LOG_LEVEL=INFO
```

### 4.6 — Criar o ambiente virtual e instalar dependências

No Terminal do VSCode, copie e cole esses comandos UM POR VEZ:

**Windows:**

```bash
python -m venv venv
```

Espere terminar. Depois:

```bash
venv\Scripts\activate
```

Deve aparecer `(venv)` no início da linha. Isso significa que o ambiente virtual está ativo.

Depois:

```bash
pip install -r requirements.txt
```

Espere instalar tudo (pode demorar 1-2 minutos).

---

**Mac/Linux:**

```bash
python3 -m venv venv
```

Depois:

```bash
source venv/bin/activate
```

Depois:

```bash
pip install -r requirements.txt
```

---

**O que é isso que acabamos de fazer?**
- `venv` = criamos uma "caixinha" isolada pro nosso projeto
- `activate` = entramos nessa caixinha
- `pip install` = instalamos as bibliotecas que o bot precisa

---

## ETAPA 5 — Rodar o Bot! 🚀

No Terminal do VSCode (com o `(venv)` aparecendo), digite:

```bash
python bot.py
```

**Se tudo der certo, você vai ver:**

```
2026-02-28 10:00:00 - __main__ - INFO - 🤖 PrazoBot iniciado!
```

**Se der erro**, veja a seção de Problemas Comuns no final.

**DEIXE ESSE TERMINAL ABERTO!** O bot só funciona enquanto esse terminal estiver rodando.

---

## ETAPA 6 — Testar o Bot! 🧪

### 6.1 — Abrir o bot no Telegram

1. Abra o **Telegram**
2. Na busca, procure o username que você criou (ex: `@prazobot_adv_bot`)
3. Clique em **"Iniciar"** ou envie `/start`

### 6.2 — Fazer o cadastro

O bot vai te perguntar:
1. **Seu nome** → digite seu nome (ex: `Maria Silva`)
2. **Sua OAB** → digite no formato número/UF (ex: `12345/CE`)

### 6.3 — Cadastrar um processo de teste

1. Envie: `/adicionar`
2. Digite um número de processo real (formato CNJ):

```
0000000-00.2024.8.06.0001
```

3. O bot vai buscar automaticamente no **DataJud do CNJ**!
4. Se encontrar, mostra os dados e pergunta se quer salvar
5. Se não encontrar, pede pra digitar manualmente

### 6.4 — Testar o briefing

Envie: `/briefing`

O bot vai gerar um resumo dos seus processos usando a ZAP IA!

### 6.5 — Fazer uma pergunta

Envie qualquer pergunta:

```
Quais são meus prazos dessa semana?
```

```
Me fala sobre o processo 0000000
```

---

## 🔁 Como parar e reiniciar o bot

**Para parar:**
- No Terminal do VSCode, aperte `Ctrl+C`

**Para reiniciar:**
1. Abra o Terminal do VSCode
2. Ative o ambiente virtual:
   - Windows: `venv\Scripts\activate`
   - Mac: `source venv/bin/activate`
3. Rode: `python bot.py`

---

## ⚙️ Configurar o envio automático de briefings

Enquanto estiver rodando na sua máquina, você pode testar o envio automático:

1. Abra um **segundo terminal** no VSCode (clique no `+` no painel de Terminal)
2. Ative o venv: `venv\Scripts\activate` (Windows) ou `source venv/bin/activate` (Mac)
3. Execute:

```bash
python scheduler.py --force
```

Isso vai enviar o briefing pra todos os advogados cadastrados, agora.

---

## 🖥️ Colocar na VPS (para rodar 24h)

Quando quiser que o bot rode 24 horas por dia sem precisar do seu computador:

### Passo 1: Criar a VPS

1. Acesse **https://www.hetzner.com/cloud** e crie uma conta
2. Clique em **"Add Server"**
3. Escolha:
   - Location: **Ashburn** ou **Helsinki** (tanto faz)
   - Image: **Ubuntu 24.04**
   - Type: **CX22** (~€4/mês) — é o mais barato e suficiente
4. Em **SSH Keys**, clique em "Add SSH Key"
   - Se não sabe o que é SSH, escolha a opção de senha mesmo
5. Clique em **"Create & Buy now"**
6. Anote o **IP** do servidor

### Passo 2: Conectar no servidor

No Terminal do VSCode:

```bash
ssh root@SEU_IP_AQUI
```

Digite a senha quando pedir.

### Passo 3: Instalar tudo no servidor

Copie e cole esses comandos no terminal conectado ao servidor, UM POR VEZ:

```bash
apt update && apt upgrade -y
```

```bash
apt install python3 python3-pip python3-venv git -y
```

```bash
mkdir prazo-bot && cd prazo-bot
```

### Passo 4: Enviar os arquivos

Do seu computador, abra OUTRO terminal e envie os arquivos:

```bash
scp -r /caminho/para/sua/pasta/prazo-bot/* root@SEU_IP:/root/prazo-bot/
```

### Passo 5: Configurar no servidor

De volta no terminal conectado ao servidor:

```bash
cd /root/prazo-bot
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

Edite o .env:

```bash
nano .env
```

Cole as mesmas configurações do seu .env local. Depois Ctrl+O pra salvar, Ctrl+X pra sair.

### Passo 6: Criar o serviço (roda pra sempre)

```bash
nano /etc/systemd/system/prazobot.service
```

Cole isso:

```
[Unit]
Description=PrazoBot Telegram
After=network.target

[Service]
Type=simple
WorkingDirectory=/root/prazo-bot
ExecStart=/root/prazo-bot/venv/bin/python bot.py
Restart=always
RestartSec=10
Environment=PYTHONUNBUFFERED=1

[Install]
WantedBy=multi-user.target
```

Salve (Ctrl+O, Enter, Ctrl+X).

Depois:

```bash
systemctl daemon-reload
systemctl enable prazobot
systemctl start prazobot
```

Verifique se está rodando:

```bash
systemctl status prazobot
```

Deve mostrar **"active (running)"** em verde!

### Passo 7: Configurar os crons

```bash
crontab -e
```

Se perguntar qual editor, escolha `1` (nano).

Adicione estas duas linhas no final:

```
0 3 * * * cd /root/prazo-bot && /root/prazo-bot/venv/bin/python atualizar.py >> /root/prazo-bot/atualizar.log 2>&1
0 * * * * cd /root/prazo-bot && /root/prazo-bot/venv/bin/python scheduler.py >> /root/prazo-bot/scheduler.log 2>&1
```

Salve (Ctrl+O, Enter, Ctrl+X).

**Pronto! O bot agora roda 24h por dia!** 🎉

---

## ❓ Problemas Comuns

### "python não é reconhecido como comando"
- Windows: reinstale o Python e marque "Add to PATH"
- Tente `python3` em vez de `python`

### "No module named 'telegram'"
- Você esqueceu de ativar o venv. Rode:
  - Windows: `venv\Scripts\activate`
  - Mac: `source venv/bin/activate`
- Depois: `pip install -r requirements.txt`

### "Error: Unauthorized" no Telegram
- O token do bot está errado no arquivo `.env`
- Pegue novamente com o @BotFather: envie `/mytoken`

### "Error" na ZAP IA
- Verifique se a URL base está correta no `.env`
- Verifique se a chave da API está correta
- Verifique se o modelo está disponível na sua conta

### O bot não responde no Telegram
- Verifique se o terminal está aberto e mostrando "PrazoBot iniciado!"
- Se fechou o terminal, o bot parou. Rode `python bot.py` de novo

### Processo não encontrado no DataJud
- Verifique se o número está no formato CNJ correto: `NNNNNNN-DD.AAAA.J.TR.OOOO`
- Alguns processos muito novos ou sigilosos não aparecem
- A chave pública do CNJ pode ter mudado: verifique em https://datajud-wiki.cnj.jus.br/api-publica/acesso

---

## 📊 Resumo dos custos

| Item | Custo |
|------|-------|
| Python | Gratuito |
| VSCode | Gratuito |
| Telegram Bot | Gratuito |
| GitLab | Gratuito |
| API DataJud (CNJ) | Gratuito |
| ZAP IA | Depende do plano da sua chave |
| VPS (quando quiser 24h) | ~R$25/mês |

---

## 📞 Checklist final

- [ ] Python instalado e funcionando
- [ ] VSCode instalado com extensão Python
- [ ] Bot criado no Telegram (tenho o token)
- [ ] Chave da ZAP IA em mãos
- [ ] Arquivos do projeto na pasta
- [ ] Arquivo .env configurado com meus dados
- [ ] Ambiente virtual criado e ativado
- [ ] Dependências instaladas (pip install)
- [ ] Bot rodando (python bot.py)
- [ ] Testei o /start no Telegram
- [ ] Cadastrei um processo de teste
- [ ] Briefing funcionando
