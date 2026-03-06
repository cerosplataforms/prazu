# 🤖 PrazorBot — Guia Passo a Passo

## Seu bot já está criado! Agora é só instalar e rodar.

**O que você já tem:**
- ✅ Bot criado no Telegram: @PrazorBot
- ✅ Token do Telegram: já configurado
- ✅ Chave da Z.AI: já configurada
- ✅ Código pronto: todos os arquivos neste pacote

**O que falta:**
- Instalar Python e VSCode no seu computador
- Copiar os arquivos pra pasta certa
- Rodar 3 comandos no terminal
- Testar!

---

## PASSO 1 — Instalar o Python (5 minutos)

### Windows:

1. Abra o navegador e acesse: **https://www.python.org/downloads/**
2. Clique no botão amarelo grande **"Download Python 3.13.x"**
3. Abra o arquivo baixado
4. **NA PRIMEIRA TELA DA INSTALAÇÃO:**

```
⬜ Use admin privileges when installing py.exe
☑️ Add python.exe to PATH     ← MARQUE ESTA CAIXINHA!!!
```

5. Clique em **"Install Now"**
6. Espere instalar e clique em "Close"

### Mac:

1. Abra o Terminal (aperte Cmd + Espaço, digite "Terminal", Enter)
2. Cole este comando e aperte Enter:

```
brew install python3
```

Se aparecer erro dizendo que brew não existe, primeiro instale o Homebrew:
- Acesse https://brew.sh e siga as instruções

---

## PASSO 2 — Instalar o VSCode (3 minutos)

1. Acesse: **https://code.visualstudio.com/**
2. Clique em **"Download"** (ele detecta seu sistema)
3. Instale (next, next, finish — tudo padrão)
4. Abra o VSCode
5. Na barra lateral esquerda, clique no ícone de **quadradinhos** (Extensions)
6. Pesquise: **Python**
7. Clique **"Install"** na extensão da Microsoft (a primeira)

---

## PASSO 3 — Preparar a pasta do projeto (5 minutos)

### 3.1 — Criar a pasta

1. Abra o **Explorador de Arquivos** (Windows) ou **Finder** (Mac)
2. Vá para **Documentos**
3. Crie uma pasta nova chamada: **prazo-bot**

### 3.2 — Extrair os arquivos

Você baixou o arquivo `prazo-bot-mvp.tar.gz`. Agora:

**Windows:**
- Clique com botão direito no arquivo → "Extrair aqui" ou "Extract All"
- Se não conseguir extrair .tar.gz, baixe o **7-Zip** grátis: https://www.7-zip.org/
- Com o 7-Zip: botão direito → 7-Zip → Extract Here (faça 2 vezes: primeiro .gz, depois .tar)
- Copie TODOS os arquivos de dentro da pasta extraída para a pasta `prazo-bot` que você criou em Documentos

**Mac:**
- Dê duplo clique no arquivo .tar.gz — ele extrai sozinho
- Copie os arquivos para a pasta `prazo-bot` em Documentos

### 3.3 — Verificar os arquivos

Sua pasta `prazo-bot` deve ter estes arquivos:

```
prazo-bot/
├── .env              ← JÁ VEM CONFIGURADO COM SEUS TOKENS!
├── .env.example
├── .gitignore
├── bot.py            ← o bot principal
├── ia.py             ← integração com Z.AI
├── database.py       ← banco de dados
├── datajud.py        ← consulta CNJ (todos os tribunais!)
├── scheduler.py      ← envio automático de briefings
├── atualizar.py      ← atualiza processos do CNJ
├── requirements.txt  ← lista de dependências
├── SETUP.md
└── GUIA-COMPLETO.md
```

**IMPORTANTE:** O arquivo `.env` já vem com seu token do Telegram e chave da Z.AI!

---

## PASSO 4 — Abrir no VSCode e instalar dependências (5 minutos)

### 4.1 — Abrir a pasta no VSCode

1. Abra o **VSCode**
2. Vá em **File → Open Folder** (ou Arquivo → Abrir Pasta)
3. Navegue até **Documentos → prazo-bot**
4. Clique em **"Selecionar Pasta"** (ou "Open")
5. Se aparecer uma pergunta sobre confiar na pasta, clique **"Yes, I trust"**

### 4.2 — Abrir o Terminal

1. No menu do VSCode: **Terminal → New Terminal**
   - Ou aperte: **Ctrl + `** (a crase, tecla ao lado do 1)
2. Um terminal vai aparecer na parte de baixo da tela
3. Ele deve mostrar o caminho da pasta:

**Windows:**
```
C:\Users\SeuNome\Documents\prazo-bot>
```

**Mac:**
```
~/Documents/prazo-bot$
```

### 4.3 — Criar o ambiente virtual

No terminal, **copie e cole** este comando e aperte **Enter**:

**Windows:**
```
python -m venv venv
```

**Mac:**
```
python3 -m venv venv
```

Espere uns segundos. Não vai aparecer nada — isso é normal.

### 4.4 — Ativar o ambiente virtual

**Windows — cole e aperte Enter:**
```
venv\Scripts\activate
```

**Mac — cole e aperte Enter:**
```
source venv/bin/activate
```

**COMO SABER SE FUNCIONOU:**
Vai aparecer `(venv)` no início da linha do terminal:

```
(venv) C:\Users\SeuNome\Documents\prazo-bot>
```

Se apareceu o `(venv)`, está certo! Se não apareceu, tente de novo.

### 4.5 — Instalar as dependências

Com o `(venv)` aparecendo, **cole e aperte Enter:**

```
pip install -r requirements.txt
```

Vai aparecer um monte de texto — é normal! Espere até aparecer "Successfully installed..." (1-2 minutos).

---

## PASSO 5 — Rodar o Bot! 🚀 (1 minuto)

No terminal (com o `(venv)` aparecendo), cole:

**Windows:**
```
python bot.py
```

**Mac:**
```
python3 bot.py
```

**SE DEU CERTO, vai aparecer:**
```
2026-02-28 xx:xx:xx - __main__ - INFO - 🤖 PrazoBot iniciado!
```

🎉 **SEU BOT ESTÁ NO AR!**

**DEIXE ESTE TERMINAL ABERTO.** Se fechar, o bot para.

---

## PASSO 6 — Testar no Telegram! 🧪

1. Abra o **Telegram** no celular ou computador
2. Procure: **@PrazorBot**
3. Clique em **"Iniciar"** ou envie `/start`
4. O bot vai pedir seu **nome** → digite (ex: `Maria Silva`)
5. Vai pedir sua **OAB** → digite (ex: `12345/CE`)
6. Pronto! Você está cadastrada!

### Cadastrar um processo:

1. Envie: `/adicionar`
2. Digite um número de processo real, ex:

```
0801234-56.2024.8.06.0001
```

3. O bot vai buscar **automaticamente no DataJud do CNJ!**
4. Se encontrar, mostra os dados e você confirma
5. Você pode adicionar um prazo (data de vencimento)

### Receber o briefing:

Envie: `/briefing`

A Z.AI vai gerar um resumo bonito dos seus processos e prazos!

### Fazer perguntas:

Envie qualquer pergunta:
- "Quais meus prazos esta semana?"
- "Me fala sobre o processo 0801234"
- "Tenho algum prazo vencendo hoje?"

---

## 🛑 Como parar e reiniciar o bot

**Parar:** No terminal do VSCode, aperte **Ctrl + C**

**Reiniciar:**
1. Abra o terminal no VSCode
2. Ative o venv:
   - Windows: `venv\Scripts\activate`
   - Mac: `source venv/bin/activate`
3. Rode: `python bot.py`

---

## ❓ Problemas e Soluções

### "python não é reconhecido"
→ Reinstale o Python e MARQUE "Add to PATH"
→ Tente `python3` em vez de `python`

### "No module named 'telegram'"
→ Você não ativou o venv. Rode:
   Windows: `venv\Scripts\activate`
   Mac: `source venv/bin/activate`
→ Depois: `pip install -r requirements.txt`

### "Unauthorized" no Telegram
→ O token pode estar errado. Abra o arquivo `.env` e verifique.

### Bot não responde no Telegram
→ O terminal deve estar aberto com "PrazoBot iniciado!"
→ Se fechou, rode `python bot.py` de novo

### "Error" na Z.AI
→ A chave pode ter expirado. Acesse https://chat.z.ai e verifique
→ Tente trocar o modelo no `.env` para `glm-4-flash`

---

## 🎯 Próximos passos

Quando o bot estiver funcionando e você quiser deixar rodando 24h:
1. Contrate uma VPS na Hetzner (~R$25/mês)
2. Me peça o passo a passo de deploy no servidor
