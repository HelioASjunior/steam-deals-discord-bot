# 🎮 SteamBot — Bot de Promoções para Discord (Python)

Bot Discord em Python que monitora e envia automaticamente **jogos gratuitos** e **promoções da Steam e Epic Games**.

---

## ✨ Funcionalidades

- 🆓 **Jogos Grátis** — Epic Games e Steam
- 🔥 **Maiores Descontos** — top descontos da Steam
- ⏰ **Envio Automático** — todo dia às 10h e 18h (Brasília)
- 🎛️ **Canal configurável** por servidor
- 📊 **Embeds ricos** com imagem, preço, desconto e botão para a loja

---

## 🚀 Instalação

### 1. Pré-requisitos
- Python 3.12+
- Conta de desenvolvedor Discord

### 2. Criar o Bot no Discord

1. Acesse [discord.com/developers/applications](https://discord.com/developers/applications)
2. **New Application** → dê um nome
3. Vá em **Bot** → clique em **Reset Token** e copie o token
4. Ative os Intents:
   - ✅ `MESSAGE CONTENT INTENT`
   - ✅ `SERVER MEMBERS INTENT`
5. Vá em **OAuth2 → URL Generator**:
   - Scopes: `bot`
   - Permissões: `Send Messages`, `Embed Links`, `Read Message History`
6. Acesse a URL gerada para **convidar** o bot

### 3. Instalar dependências

- python -m venv venv
- venv\Scripts\activate   # Windows

```bash
pip install -r requirements.txt
```

### 4. Configurar o token

```bash
cp .env.example .env
```

Edite `.env` e cole seu token:
```
DISCORD_TOKEN=seu_token_aqui
```

### 5. Rodar

```bash
python bot.py
```

---

## 🎮 Comandos

| Comando | Descrição | Permissão |
|---------|-----------|-----------|
| `!setcanal [#canal]` | Define o canal de promoções automáticas | Admin |
| `!promo` | Envia promoções imediatamente | Admin |
| `!gratis` | Mostra jogos gratuitos agora | Todos |
| `!deals` | Mostra maiores descontos da Steam | Todos |
| `!ajuda` | Lista os comandos | Todos |

---

## 📡 APIs utilizadas (gratuitas, sem chave)

- **CheapShark** — promoções e gratuitos da Steam
- **Epic Games Store API** — jogos grátis da semana

---

## 💡 Uso rápido

1. Inicie o bot: `python bot.py`
2. No Discord: `!setcanal #promoções`
3. Para testar: `!promo`
4. Automático: todo dia às **10h e 18h**
