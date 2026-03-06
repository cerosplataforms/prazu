# PrazoBot MVP — Guia de Setup

## 🚀 Setup Rápido (na sua máquina)

### 1. Criar o Bot no Telegram

1. Abra o Telegram e procure **@BotFather**
2. Envie `/newbot`
3. Escolha um nome: `PrazoBot` (ou o que quiser)
4. Escolha um username: `prazobot_adv_bot` (precisa terminar com `_bot`)
5. Copie o **token** que ele vai te dar

### 2. Instalar dependências

```bash
# Clone ou copie os arquivos pra uma pasta
cd prazo-bot

# Crie um ambiente virtual (recomendado)
python3 -m venv venv
source venv/bin/activate   # Linux/Mac
# venv\Scripts\activate    # Windows

# Instale as dependências
pip install -r requirements.txt
```

### 3. Configurar o .env

```bash
cp .env.example .env
nano .env   # ou abra no editor de sua preferência
```

Preencha:
- `TELEGRAM_TOKEN` — o token do BotFather
- `ZAPIA_API_KEY` — sua chave da ZAP IA
- `ZAPIA_BASE_URL` — URL da API da ZAP IA (verifique na documentação deles)
- `ZAPIA_MODEL` — o modelo que sua chave permite usar

> **⚠️ IMPORTANTE sobre a ZAP IA:**
> A ZAP IA pode usar diferentes formatos de API. O código está preparado
> para APIs compatíveis com o formato OpenAI. Se a ZAP IA usar outro formato,
> você precisará ajustar o arquivo `ia.py`. Verifique na documentação deles:
> - Qual a URL base da API
> - Qual o formato de autenticação (Bearer token, API key header, etc)
> - Quais modelos estão disponíveis

### 4. Rodar o bot

```bash
python bot.py
```

Pronto! Agora vá no Telegram, procure seu bot e envie `/start`.

### 5. Configurar o Briefing Automático (Cron)

O scheduler precisa rodar a cada hora pra checar quem deve receber briefing:

```bash
# Edite o crontab
crontab -e

# Adicione esta linha (roda a cada hora cheia):
0 * * * * cd /caminho/para/prazo-bot && /caminho/para/venv/bin/python scheduler.py >> /var/log/prazobot.log 2>&1
```

Para testar o envio manual:
```bash
python scheduler.py --force
```

---

## 🖥️ Deploy na VPS (Hetzner/Contabo/DigitalOcean)

### 1. Criar a VPS

- Ubuntu 22.04 ou 24.04
- Plano mais barato (2 vCPU, 2-4GB RAM é mais que suficiente)
- Hetzner: ~€4/mês | Contabo: ~€5/mês

### 2. Setup inicial na VPS

```bash
# Conecte via SSH
ssh root@seu-ip

# Atualize
apt update && apt upgrade -y

# Instale Python
apt install python3 python3-pip python3-venv git -y

# Crie um usuário pro bot (boa prática)
adduser prazobot
su - prazobot

# Clone/copie o projeto
mkdir prazo-bot && cd prazo-bot
# (copie os arquivos via scp ou git)

# Setup do ambiente
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Configure o .env
cp .env.example .env
nano .env
```

### 3. Rodar como serviço (systemd)

Crie o arquivo de serviço:

```bash
sudo nano /etc/systemd/system/prazobot.service
```

Conteúdo:

```ini
[Unit]
Description=PrazoBot Telegram
After=network.target

[Service]
Type=simple
User=prazobot
WorkingDirectory=/home/prazobot/prazo-bot
ExecStart=/home/prazobot/prazo-bot/venv/bin/python bot.py
Restart=always
RestartSec=10
Environment=PYTHONUNBUFFERED=1

[Install]
WantedBy=multi-user.target
```

Ative:

```bash
sudo systemctl daemon-reload
sudo systemctl enable prazobot
sudo systemctl start prazobot

# Ver logs:
sudo journalctl -u prazobot -f
```

### 4. Configurar o Cron na VPS

```bash
crontab -e

# Briefing a cada hora
0 * * * * cd /home/prazobot/prazo-bot && /home/prazobot/prazo-bot/venv/bin/python scheduler.py >> /home/prazobot/prazo-bot/scheduler.log 2>&1
```

---

## 📁 Estrutura do Projeto

```
prazo-bot/
├── bot.py              # Bot Telegram principal
├── ia.py               # Integração com ZAP IA
├── database.py         # Banco de dados SQLite
├── scheduler.py        # Envio automático dos briefings
├── requirements.txt    # Dependências Python
├── .env.example        # Template de configuração
├── .env                # Suas configurações (NÃO commitar)
├── prazobot.db         # Banco SQLite (criado automaticamente)
└── SETUP.md            # Este arquivo
```

---

## 🧪 Testando

1. Abra o bot no Telegram → `/start`
2. Cadastre-se com nome e OAB
3. Use `/adicionar` para cadastrar um processo de teste
4. Adicione um prazo que vence hoje
5. Use `/briefing` para testar o briefing
6. Faça perguntas: "Quais meus prazos dessa semana?"
7. Rode `python scheduler.py --force` para testar o envio automático

---

## 🔧 Ajustes na ZAP IA

Se a ZAP IA tiver um formato diferente do OpenAI, edite `ia.py`:

```python
# Se a ZAP IA usar requests direto em vez do SDK OpenAI:
import requests

def chamar_zapia(prompt):
    response = requests.post(
        "https://URL-DA-ZAPIA/chat",
        headers={
            "Authorization": f"Bearer {ZAPIA_API_KEY}",
            "Content-Type": "application/json"
        },
        json={
            "messages": [{"role": "user", "content": prompt}],
            "model": "modelo-disponivel"
        }
    )
    return response.json()["choices"][0]["message"]["content"]
```

Verifique a documentação da ZAP IA para o formato correto.

---

## 📊 Próximos Passos (depois de validar)

- [ ] Integrar consulta automática aos tribunais (DataJud, ESAJ)
- [ ] Adicionar monitoramento de publicações (DJE)
- [ ] Migrar para WhatsApp (API Business)
- [ ] Landing page para captação
- [ ] Sistema de pagamentos
- [ ] Dashboard web
