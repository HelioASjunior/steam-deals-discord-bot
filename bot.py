import discord
from discord.ext import commands, tasks
import aiohttp
import json
import os
from datetime import datetime, time
import asyncio
from dotenv import load_dotenv

load_dotenv()
TOKEN = os.getenv("DISCORD_TOKEN")

# ─── Setup ────────────────────────────────────────────────────────────────────
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents, help_command=None)

# ─── Persistência ─────────────────────────────────────────────────────────────
DATA_FILE = "data.json"

def load_data():
    if not os.path.exists(DATA_FILE):
        with open(DATA_FILE, "w") as f:
            json.dump({"channels": {}}, f)
    with open(DATA_FILE) as f:
        return json.load(f)

def save_data(data):
    with open(DATA_FILE, "w") as f:
        json.dump(data, f, indent=2)

# ─── API: Jogos grátis da Epic Games ──────────────────────────────────────────
async def get_epic_free_games():
    url = (
        "https://store-site-backend-static.ak.epicgames.com/freeGamesPromotions"
        "?locale=pt-BR&country=BR&allowCountries=BR"
    )
    try:
        async with aiohttp.ClientSession() as s:
            async with s.get(url, timeout=aiohttp.ClientTimeout(total=10)) as r:
                data = await r.json(content_type=None)

        elements = (
            data.get("data", {})
                .get("Catalog", {})
                .get("searchStore", {})
                .get("elements", [])
        )
        result = []
        for g in elements:
            promos = (g.get("promotions") or {}).get("promotionalOffers", [])
            if not promos:
                continue
            offers = promos[0].get("promotionalOffers", [])
            if not offers:
                continue
            price = g.get("price", {}).get("totalPrice", {}).get("discountPrice", 1)
            if price != 0:
                continue

            orig = g.get("price", {}).get("totalPrice", {}).get("originalPrice", 0)
            img = next(
                (i["url"] for i in g.get("keyImages", [])
                 if i["type"] in ("OfferImageWide", "Thumbnail")), ""
            )
            slug = g.get("productSlug") or g.get("urlSlug", "")
            end_date = offers[0].get("endDate", "")[:10]

            result.append({
                "title": g["title"],
                "desc": (g.get("description") or "Jogo gratuito por tempo limitado!")[:180],
                "image": img,
                "url": f"https://store.epicgames.com/pt-BR/p/{slug}",
                "original_price": f"R$ {orig/100:.2f}" if orig else "Pago",
                "end_date": end_date,
                "source": "Epic Games",
            })
        return result
    except Exception as e:
        print(f"[Epic] Erro: {e}")
        return []

# ─── API: Jogos 100% off na Steam (CheapShark) ────────────────────────────────
async def get_steam_free_games():
    url = "https://www.cheapshark.com/api/1.0/deals?storeID=1&upperPrice=0&pageSize=5"
    try:
        async with aiohttp.ClientSession() as s:
            async with s.get(url, timeout=aiohttp.ClientTimeout(total=10)) as r:
                data = await r.json()
        result = []
        for d in data:
            result.append({
                "title": d["title"],
                "desc": "Jogo gratuito na Steam agora!",
                "image": f"https://cdn.cloudflare.steamstatic.com/steam/apps/{d['steamAppID']}/header.jpg",
                "url": f"https://store.steampowered.com/app/{d['steamAppID']}",
                "original_price": f"${d['normalPrice']}",
                "source": "Steam",
            })
        return result
    except Exception as e:
        print(f"[Steam Free] Erro: {e}")
        return []

# ─── API: Maiores descontos da Steam ──────────────────────────────────────────
async def get_steam_big_deals():
    url = "https://www.cheapshark.com/api/1.0/deals?storeID=1&pageSize=8&sortBy=Savings&desc=1"
    try:
        async with aiohttp.ClientSession() as s:
            async with s.get(url, timeout=aiohttp.ClientTimeout(total=10)) as r:
                data = await r.json()
        result = []
        for d in data:
            result.append({
                "title": d["title"],
                "image": f"https://cdn.cloudflare.steamstatic.com/steam/apps/{d['steamAppID']}/header.jpg",
                "url": f"https://store.steampowered.com/app/{d['steamAppID']}",
                "original_price": f"${d['normalPrice']}",
                "sale_price": f"${d['salePrice']}",
                "discount": f"{round(float(d['savings']))}",
                "metacritic": d["metacriticScore"] if d["metacriticScore"] != "0" else None,
                "source": "Steam",
            })
        return result
    except Exception as e:
        print(f"[Steam Deals] Erro: {e}")
        return []

# ─── Embeds ───────────────────────────────────────────────────────────────────
def embed_free(game: dict) -> discord.Embed:
    embed = discord.Embed(
        title=f"🎮 {game['title']}",
        description=game.get("desc", ""),
        color=0x1b2838,
        url=game["url"],
    )
    embed.add_field(name="💰 Preço", value=f"~~{game['original_price']}~~ → **GRÁTIS**", inline=True)
    embed.add_field(name="🏪 Plataforma", value=game["source"], inline=True)
    if game.get("end_date"):
        embed.add_field(name="⏳ Válido até", value=game["end_date"], inline=True)
    if game.get("image"):
        embed.set_image(url=game["image"])
    embed.set_footer(text="SteamBot • Ofertas Gamers 🎮")
    embed.timestamp = datetime.utcnow()
    return embed

def embed_deal(game: dict) -> discord.Embed:
    embed = discord.Embed(
        title=f"🔥 {game['title']}",
        color=0xc2703f,
        url=game["url"],
    )
    embed.add_field(name="💸 De", value=game["original_price"], inline=True)
    embed.add_field(name="💰 Por", value=game.get("sale_price", "GRÁTIS"), inline=True)
    embed.add_field(name="🏷️ Desconto", value=f"**{game['discount']}% OFF**", inline=True)
    if game.get("metacritic"):
        embed.add_field(name="🎯 Metacritic", value=game["metacritic"], inline=True)
    if game.get("image"):
        embed.set_image(url=game["image"])
    embed.set_footer(text="SteamBot • Ofertas Gamers 🎮")
    embed.timestamp = datetime.utcnow()
    return embed

def btn_link(label: str, url: str) -> discord.ui.View:
    view = discord.ui.View()
    view.add_item(discord.ui.Button(label=label, url=url, style=discord.ButtonStyle.link))
    return view

# ─── Enviar promoções para todos os canais ────────────────────────────────────
async def send_promotions(guild_id: str = None):
    data = load_data()
    targets = {guild_id: data["channels"][guild_id]} if guild_id else data["channels"]

    for gid, config in targets.items():
        ch_id = config.get("channel_id")
        if not ch_id:
            continue
        channel = bot.get_channel(int(ch_id))
        if not channel:
            continue

        # Header
        header = discord.Embed(
            title="🎮 Novidades de Jogos — Steam & Epic",
            description="Aqui estão as melhores promoções e jogos **gratuitos** de hoje!",
            color=0x1b2838,
        )
        header.set_thumbnail(url="https://store.steampowered.com/favicon.ico")
        header.timestamp = datetime.utcnow()
        await channel.send(embed=header)

        # Jogos grátis
        free_games = await get_epic_free_games() + await get_steam_free_games()
        if free_games:
            await channel.send("## 🆓 Jogos Gratuitos Agora!")
            for g in free_games:
                await channel.send(embed=embed_free(g), view=btn_link("🛒 Pegar Grátis", g["url"]))
                await asyncio.sleep(0.8)

        # Maiores descontos
        deals = await get_steam_big_deals()
        if deals:
            await channel.send("## 🔥 Maiores Descontos da Steam")
            for d in deals:
                await channel.send(embed=embed_deal(d), view=btn_link("🛒 Ver na Steam", d["url"]))
                await asyncio.sleep(0.8)

        await channel.send(
            embed=discord.Embed(
                description="✅ Isso é tudo! Próxima atualização automática em breve.",
                color=0x57f287,
            )
        )

# ─── Tarefa automática: 10h e 18h (Brasília = UTC-3) ─────────────────────────
@tasks.loop(time=[time(13, 0), time(21, 0)])  # 10h e 18h BRT = 13h e 21h UTC
async def auto_promotions():
    print(f"[{datetime.now().strftime('%H:%M')}] Enviando promoções automáticas...")
    await send_promotions()

# ─── Comandos ─────────────────────────────────────────────────────────────────
@bot.command(name="setcanal")
@commands.has_permissions(administrator=True)
async def set_channel(ctx, channel: discord.TextChannel = None):
    """Define o canal de promoções automáticas."""
    target = channel or ctx.channel
    data = load_data()
    data["channels"].setdefault(str(ctx.guild.id), {})["channel_id"] = str(target.id)
    save_data(data)
    await ctx.reply(f"✅ Canal de promoções definido: {target.mention}")

@bot.command(name="promo")
@commands.has_permissions(administrator=True)
async def force_promo(ctx):
    """Envia promoções agora no canal configurado."""
    data = load_data()
    if str(ctx.guild.id) not in data["channels"]:
        return await ctx.reply("❌ Nenhum canal configurado. Use `!setcanal #canal` primeiro.")
    await ctx.reply("⏳ Buscando promoções, aguarde...")
    await send_promotions(str(ctx.guild.id))

@bot.command(name="gratis")
async def free_games(ctx):
    """Mostra jogos gratuitos no momento."""
    await ctx.reply("🔍 Buscando jogos gratuitos...")
    games = await get_epic_free_games() + await get_steam_free_games()
    if not games:
        return await ctx.reply("😔 Nenhum jogo gratuito encontrado agora.")
    for g in games[:5]:
        await ctx.channel.send(embed=embed_free(g), view=btn_link("🛒 Pegar Grátis", g["url"]))

@bot.command(name="deals")
async def big_deals(ctx):
    """Mostra os maiores descontos da Steam."""
    await ctx.reply("🔍 Buscando melhores promoções...")
    deals = await get_steam_big_deals()
    if not deals:
        return await ctx.reply("😔 Nenhuma promoção encontrada agora.")
    for d in deals[:5]:
        await ctx.channel.send(embed=embed_deal(d), view=btn_link("🛒 Ver na Steam", d["url"]))

@bot.command(name="ajuda")
async def ajuda(ctx):
    """Lista todos os comandos."""
    embed = discord.Embed(title="🤖 Comandos do SteamBot", color=0x1b2838)
    embed.add_field(name="`!setcanal [#canal]`", value="Define o canal de promoções automáticas *(Admin)*", inline=False)
    embed.add_field(name="`!promo`",             value="Envia promoções agora no canal configurado *(Admin)*", inline=False)
    embed.add_field(name="`!gratis`",            value="Mostra jogos gratuitos no momento", inline=False)
    embed.add_field(name="`!deals`",             value="Mostra os maiores descontos da Steam", inline=False)
    embed.add_field(name="`!ajuda`",             value="Mostra esta mensagem", inline=False)
    embed.set_footer(text="Envio automático: todo dia às 10h e 18h (Brasília)")
    await ctx.reply(embed=embed)

# ─── Tratamento de erros ──────────────────────────────────────────────────────
@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.MissingPermissions):
        await ctx.reply("❌ Você precisa ser **administrador** para usar este comando.")
    elif isinstance(error, commands.CommandNotFound):
        pass  # ignora comandos desconhecidos
    else:
        print(f"Erro: {error}")

# ─── Iniciar ──────────────────────────────────────────────────────────────────
@bot.event
async def on_ready():
    print(f"✅ Bot online como {bot.user} ({bot.user.id})")
    await bot.change_presence(
        activity=discord.Activity(type=discord.ActivityType.watching, name="🎮 promoções da Steam")
    )
    auto_promotions.start()

bot.run(TOKEN)
