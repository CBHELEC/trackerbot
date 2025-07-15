from pathlib import Path
from dotenv import load_dotenv
load_dotenv(verbose=True, override=True)

import os
import discord
import ezcord
import uvicorn
import requests
import io
from discord.ext.ipc import Client
from fastapi import Cookie, FastAPI, HTTPException, Request, Body
from fastapi.responses import RedirectResponse, JSONResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from starlette.templating import Jinja2Templates
from contextlib import asynccontextmanager
from backend import DiscordAuth, db, feature_db
from database import *
from PIL import Image, ImageDraw, ImageFont
from datetime import datetime
from urllib.parse import quote
from jinja2 import Environment, FileSystemLoader

CLIENT_ID = os.getenv('CLIENT_ID')
CLIENT_SECRET = os.getenv('CLIENT_SECRET')
REDIRECT_URI = os.getenv('REDIRECT_URI')
SECRET_KEY = os.getenv('SECRET_KEY')

LOGIN_URL = f"https://discord.com/oauth2/authorize?client_id={CLIENT_ID}&response_type=code&redirect_uri={quote(REDIRECT_URI, safe='')}&scope=identify+guilds"
INVITE_LINK = f"https://discord.com/oauth2/authorize?client_id={CLIENT_ID}"

@asynccontextmanager
async def on_startup(app: FastAPI):
    await api.setup()
    await db.setup()
    await feature_db.setup()

    yield

    await api.close()

app = FastAPI(lifespan=on_startup)
app.mount("/static", StaticFiles(directory=Path(__file__).parent / "frontend/static"), name="static")
templates = Jinja2Templates(directory=Path(__file__).parent / "frontend")
TEMPLATE_DIR = Path(__file__).parent / "frontend" / "static" / "templates"
env = Environment(loader=FileSystemLoader(str(TEMPLATE_DIR)))
embed_data = {}

ipc = Client(secret_key=SECRET_KEY)
api = DiscordAuth(CLIENT_ID, CLIENT_SECRET, REDIRECT_URI)


@app.get("/")
async def home(request: Request):
    session_id = request.cookies.get("session_id")
    if session_id and await db.get_session(session_id):
        return RedirectResponse(url="/guilds")

    guild_count = await ipc.request("guild_count")
    return templates.TemplateResponse(
        "index.html",
        {
            "request": request,
            "count": guild_count.response,
            "login_url": LOGIN_URL
        }
    )


@app.get("/callback")
async def callback(code: str):
    data = {
        "client_id": CLIENT_ID,
        "client_secret": CLIENT_SECRET,
        "grant_type": "authorization_code",
        "code": code,
        "redirect_uri": REDIRECT_URI,
    }

    result = await api.get_token_response(data)
    if result is None:
        raise HTTPException(status_code=401, detail="Invalid Auth Code")

    token, refresh_token, expires_in = result
    user = await api.get_user(token)
    user_id = user.get("id")

    session_id = await db.add_session(token, refresh_token, expires_in, user_id)

    response = RedirectResponse(url="/guilds")
    response.set_cookie(key="session_id", value=session_id, httponly=True)
    return response


@app.get("/guilds")
async def guilds(request: Request):
    session_id = request.cookies.get("session_id")
    session = await db.get_session(session_id)
    if not session_id or not session:
        raise HTTPException(status_code=401, detail="no auth")

    token, refresh_token, token_expires_at = session

    user = await api.get_user(token)
    if datetime.now() > token_expires_at or user.get("code") == 0:
        if await api.reload(session_id, refresh_token):
            RedirectResponse(url="/guilds")
        else:
            RedirectResponse(url="/logout")

    if "id" not in user:
        return RedirectResponse(url="/logout")

    user_guilds = await api.get_guilds(token)
    bot_guilds = await ipc.request("bot_guilds")
    perms = []

    guilds_with_bot = []
    guilds_without_bot = []

    for guild in user_guilds:
        bot_in_guild = guild["id"] in bot_guilds.response["data"]
        guild["bot_in_guild"] = bot_in_guild

        if guild["icon"]:
            guild["icon"] = f"https://cdn.discordapp.com/icons/{guild['id']}/{guild['icon']}"
        else:
            guild["icon"] = ezcord.random_avatar()

        is_admin = discord.Permissions(int(guild["permissions"])).administrator
        if is_admin or guild["owner"]:
            if bot_in_guild:
                guild["url"] = f"/server/{guild['id']}"
                guilds_with_bot.append(guild)
            else:
                guild["url"] = f"{INVITE_LINK}&guild_id={guild['id']}"
                guilds_without_bot.append(guild)

    return templates.TemplateResponse(
        "guilds.html",
        {
            "request": request,
            "global_name": user["global_name"],
            "avatar_hash": user["avatar"],
            "user_id": user["id"],
            "guilds_with_bot": guilds_with_bot,
            "guilds_without_bot": guilds_without_bot
        }
    )

DISCORD_API_BASE = "https://discord.com/api/v10"

def rounded_rectangle(im, radius):
    circle = Image.new("L", (radius * 2, radius * 2), 0)
    draw = ImageDraw.Draw(circle)
    draw.ellipse((0, 0, radius * 2, radius * 2), fill=255)
    alpha = Image.new("L", im.size, 255)
    w, h = im.size
    alpha.paste(circle.crop((0, 0, radius, radius)), (0, 0))
    alpha.paste(circle.crop((0, radius, radius, radius * 2)), (0, h - radius))
    alpha.paste(circle.crop((radius, 0, radius * 2, radius)), (w - radius, 0))
    alpha.paste(circle.crop((radius, radius, radius * 2, radius * 2)), (w - radius, h - radius))
    im.putalpha(alpha)
    return im

def get_discord_user(user_id: str):
    from dotenv import load_dotenv
    load_dotenv(Path(__file__).parent / ".env")
    TOKEN = os.getenv("TOKEN")
    url = f"{DISCORD_API_BASE}/users/{user_id}"
    headers = {"Authorization": f"Bot {TOKEN}"} 
    r = requests.get(url, headers=headers)
    if r.status_code != 200:
        raise HTTPException(status_code=404, detail="User not found")
    return r.json()

def get_avatar_image(user):
    avatar_hash = user.get("avatar")
    user_id = user["id"]
    user_status = user.get("status", "invisible").lower()

    if avatar_hash:
        ext = "gif" if avatar_hash.startswith("a_") else "png"
        url = f"https://cdn.discordapp.com/avatars/{user_id}/{avatar_hash}.{ext}?size=128"
    else:
        default_avatar_num = int(user_id) % 5
        url = f"https://cdn.discordapp.com/embed/avatars/{default_avatar_num}.png"

    try:
        resp = requests.get(url)
        resp.raise_for_status()
        avatar = Image.open(io.BytesIO(resp.content)).convert("RGBA")
        avatar = avatar.resize((80, 80), Image.LANCZOS)

        # Step 1: Apply circular mask
        mask = Image.new("L", (80, 80), 0)
        draw = ImageDraw.Draw(mask)
        draw.ellipse((0, 0, 80, 80), fill=255)

        # Step 2: Cut out bottom-right corner for status dot
        dot_radius = 10
        dot_box = (80 - 2*dot_radius, 80 - 2*dot_radius, 80, 80)
        draw.ellipse(dot_box, fill=0)

        avatar.putalpha(mask)
        return avatar
    except:
        fallback = Image.new("RGBA", (80, 80), (150, 150, 150, 255))
        mask = Image.new("L", (80, 80), 0)
        draw = ImageDraw.Draw(mask)
        draw.ellipse((0, 0, 80, 80), fill=255)
        fallback.putalpha(mask)
        return fallback

def draw_paragraph(draw, text, font, x, y, max_width, fill=(255, 255, 255), line_spacing=4):
    def get_text_size(text):
        bbox = font.getbbox(text)
        width = bbox[2] - bbox[0]
        height = bbox[3] - bbox[1]
        return width, height

    words = text.split()
    lines = []
    line = ""

    for word in words:
        test_line = line + (" " if line else "") + word
        line_width, _ = get_text_size(test_line)
        if line_width <= max_width:
            line = test_line
        else:
            lines.append(line)
            line = word

    if line:
        lines.append(line)

    for i, line in enumerate(lines):
        draw.text((x, y + i * (font.size + line_spacing)), line, font=font, fill=fill)

@app.get("/embed/image/{user_id}.png")
async def embed_image(user_id: str):
    user = get_discord_user(user_id)
    username = user["global_name"]
    if not username:
        username = user["username"]
    u_status = await ipc.request("get_user_status", user_id=user_id)
    status = (u_status.response or {}).get("status", "invisible")

    width, height = 1225, 210  # Increased height
    bg_color = (54, 57, 63)
    text_color = (255, 255, 255)
    subtext_color = (180, 180, 180)

    img = Image.new("RGBA", (width, height), bg_color)
    img = rounded_rectangle(img, 20)
    draw = ImageDraw.Draw(img)

    base_dir = os.path.dirname(os.path.abspath(__file__))
    font_path = os.path.join(base_dir, "frontend", "static", "NotoSansCJKRegular.otf")
    para_font = ImageFont.truetype(font_path, 14)
    font_main = ImageFont.truetype(font_path, 24)
    font_sub = ImageFont.truetype(font_path, 16)

    avatar = get_avatar_image(user)
    avatar_x, avatar_y = 20, 20
    img.paste(avatar, (avatar_x, avatar_y), avatar)
    base_dir = os.path.dirname(os.path.abspath(__file__)) 

    status_path = {
        "online": os.path.join(base_dir, "frontend", "static", "ONLINE.png"),
        "idle": os.path.join(base_dir, "frontend", "static", "IDLE.png"),
        "invisible": os.path.join(base_dir, "frontend", "static", "OFFLINE.png"),
        "dnd": os.path.join(base_dir, "frontend", "static", "DO_NOT_DISTURB.png"),
    }.get(status, os.path.join(base_dir, "frontend", "static", "OFFLINE.png"))

    if status_path:
        dot_icon = Image.open(status_path).convert("RGBA").resize((20, 20), Image.LANCZOS)

        dot_x = avatar_x + 80 - dot_icon.width
        dot_y = avatar_y + 80 - dot_icon.height

        border_circle = Image.new("RGBA", (24, 24), (0, 0, 0, 0))
        ImageDraw.Draw(border_circle).ellipse((0, 0, 23, 23), fill=(54, 57, 63))

        img.paste(border_circle, (dot_x - 2, dot_y - 2), border_circle)
        img.paste(dot_icon, (dot_x, dot_y), dot_icon)

    text_x = 120
    draw.text((text_x, 30), username, font=font_main, fill=text_color)

    servercount = await ipc.request("guild_count")

    if user_id == "820297275448098817":
        draw.text((text_x, 65), "Lead Developer & Founder", font=font_sub, fill=subtext_color)
        draw.text((text_x, 90), "he/him, British", font=font_sub, fill=subtext_color)
        paragraph_text = f"Heya – I’m CBH. I started this bot in December of 2024, and it just kept growing. Now, it is in {servercount.response} servers, and the updates keep rolling. I have always had a passion for technology and started coding python in August of 2024. I am a furry, and my fursona species is a mix between a wolf / dog. In terms of Geocaching, I (as of writing this) have 160 finds, 11 hides and love to collect geocoins, the cool expensive trackable coins. Right now, I have 25 geocoins, and my favourites are the Mardi Gras mask coins - I am working on collecting all of them! Anyways… that’s it for now, happy caching folks!"
    elif user_id == "966167498011598858":
        draw.text((text_x, 65), "Bugfixer & Tester", font=font_sub, fill=subtext_color)
        font_sub_a_path = os.path.join(base_dir, "frontend", "static", "Symbola.ttf")
        font_sub_a = ImageFont.truetype(font_sub_a_path, size=20)

        clef = "𝄢"
        slash = "/"
        y = 90

        clef1_x = text_x + 12
        slash_x = text_x + 9   
        clef2_x = text_x + 28   
        canadian_x = text_x + 25  

        draw.text((clef1_x, y), clef, font=font_sub_a, fill=subtext_color)
        draw.text((slash_x, y - 2), slash, font=font_sub, fill=subtext_color)
        draw.text((clef2_x, y), clef, font=font_sub_a, fill=subtext_color)
        draw.text((canadian_x, y), ", Canadian", font=font_sub, fill=subtext_color)
        paragraph_text = "i love music"
    elif user_id == "1081379243948265602":
        draw.text((text_x, 65), "Artist & Tester", font=font_sub, fill=subtext_color)
        draw.text((text_x, 90), "he/him, Canadian", font=font_sub, fill=subtext_color)
        paragraph_text = "I'm Artist/Designer for this project, and a geocacher from the province of Alberta. We're a team of geocachers with a little over 300 finds, and we've been caching since 2024. As of right now, a newer passion of mine is collecting geocoins—right now we only have one, but we hope to grow our collection in the future!"
    elif user_id == "768519177954131988":
        draw.text((text_x, 65), "Tester & Helper", font=font_sub, fill=subtext_color)
        draw.text((text_x, 90), "??/??, ??", font=font_sub, fill=subtext_color)
        paragraph_text = "this will change, but mikaboo is on break sadly and unconctactable. we liek mikaboo though. mikaboo is good."
    elif user_id == "374283134243700747":
        draw.text((text_x, 65), "Assistant Developer", font=font_sub, fill=subtext_color)
        draw.text((text_x, 90), "??/??, ??", font=font_sub, fill=subtext_color)
        paragraph_text = "we <3 democat"

    below_avatar_x = avatar_x
    below_avatar_y = avatar_y + 80 + 20  # avatar + spacing
    below_avatar_width = width - 2 * avatar_x
    below_avatar_height = height - below_avatar_y - 20

    draw_paragraph(draw, paragraph_text, para_font, below_avatar_x, below_avatar_y, below_avatar_width, below_avatar_height)

    buf = io.BytesIO()
    img.save(buf, format="PNG")
    buf.seek(0)
    return StreamingResponse(buf, media_type="image/png")

@app.get("/server/{guild_id}")
async def server(request: Request, guild_id: int):
    session_id = request.cookies.get("session_id")
    if not session_id or not await db.get_session(session_id):
        raise HTTPException(status_code=401, detail="no auth")

    stats = await ipc.request("guild_stats", guild_id=guild_id)
    setting = get_guild_settings(guild_id)
    if setting:
        feature_txt = setting.skullboard_channel_id
        selected_roles = setting.perm_role_ids.split(",") if setting.perm_role_ids else []
        detection_status = bool(setting.detection_status) if hasattr(setting, 'detection_status') else True
        link_embed_status = bool(setting.link_embed_status) if hasattr(setting, 'link_embed_status') else True
        message_set = int(setting.message_set) if hasattr(setting, 'message_set') else 1
        tb_set = int(setting.tb_set) if hasattr(setting, 'tb_set') else 1
        fun_set = int(setting.fun_set) if hasattr(setting, 'fun_set') else 1
        game_set = int(setting.game_set) if hasattr(setting, 'game_set') else 1
    else:
        feature_txt = "Feature is not set."
        selected_roles = []
        detection_status = True
        link_embed_status = True
        message_set = 1
        tb_set = 1
        fun_set = 1
        game_set = 1

    session_id = request.cookies.get("session_id")
    session = await db.get_session(session_id)
    if not session_id or not session:
        raise HTTPException(status_code=401, detail="no auth")

    token, refresh_token, token_expires_at = session
    user = await api.get_user(token)

    icon_hash = (await ipc.request("guild_icon_hash", guild_id=guild_id)).response["guild_icon_hash"]
    guild_icon_url = f"https://cdn.discordapp.com/icons/{guild_id}/{icon_hash}.png?size=1024" if icon_hash else ezcord.random_avatar()

    categories_resp = await ipc.request("guild_categories", guild_id=guild_id)
    categories = categories_resp.response["categories"] if categories_resp and "categories" in categories_resp.response else []

    channels_resp = await ipc.request("guild_channels", guild_id=guild_id)
    channels = channels_resp.response["channels"] if channels_resp and "channels" in channels_resp.response else []

    roles_resp = await ipc.request("guild_roles", guild_id=guild_id)
    roles = []
    if roles_resp and roles_resp.response and "roles" in roles_resp.response:
        roles = roles_resp.response["roles"]

    return templates.TemplateResponse(
        "server.html",
        {
            "request": request,
            "name": stats.response["name"],
            "count": stats.response["member_count"],
            "id": guild_id,
            "feature": feature_txt,
            "categories": categories,
            "channels": channels,
            "roles": roles,
            "selected_roles": selected_roles,
            "global_name": user["global_name"],
            "avatar_hash": user["avatar"],
            "user_id": user["id"],
            "guild_icon_url": guild_icon_url,
            "detection_status": detection_status,
            "embed_status": link_embed_status,
            "message_set": message_set,
            "tb_set": tb_set,
            "fun_set": fun_set,
            "game_set": game_set,
        },
    )

@app.get("/server/{guild_id}/settings/set_channel/{channel_id}")
async def set_channel(guild_id: int, channel_id: str, session_id: str = Cookie(None)):
    user_id = await db.get_user_id(session_id)
    if not session_id or not user_id:
        raise HTTPException(status_code=401, detail="no auth")

    perms = await ipc.request("check_perms", guild_id=guild_id, user_id=user_id)
    if not perms.response.get("perms"):
        return {"error": "You do not have access to this server"}

    if channel_id == "none":
        update_guild_settings(guild_id, skullboard_status=False, skullboard_channel_id=None)
    else:
        update_guild_settings(guild_id, skullboard_status=True, skullboard_channel_id=str(channel_id))
    return RedirectResponse(url=f"/server/{guild_id}")

@app.get("/server/{guild_id}/settings/set_perm/{role_id}")
async def set_perm(guild_id: int, role_id: str, session_id: str = Cookie(None)):
    user_id = await db.get_user_id(session_id)
    if not session_id or not user_id:
        raise HTTPException(status_code=401, detail="no auth")

    perms = await ipc.request("check_perms", guild_id=guild_id, user_id=user_id)
    if not perms.response.get("perms"):
        return {"error": "You do not have access to this server"}

    return RedirectResponse(url=f"/server/{guild_id}")

@app.post("/server/{guild_id}/settings/set_perm_roles")
async def set_perm_roles(guild_id: int, request: Request, session_id: str = Cookie(None), body: dict = Body(...)):
    user_id = await db.get_user_id(session_id)
    if not session_id or not user_id:
        raise HTTPException(status_code=401, detail="no auth")

    perms = await ipc.request("check_perms", guild_id=guild_id, user_id=user_id)
    if not perms.response.get("perms"):
        return JSONResponse({"error": "You do not have access to this server"}, status_code=403)

    role_ids = body.get("role_ids", [])
    update_guild_settings(guild_id, perm_role_ids=",".join(role_ids))
    return JSONResponse({"success": True})

@app.get("/server/{guild_id}/settings/toggle_detection/{status}")
async def set_channel(guild_id: int, status: int, session_id: str = Cookie(None)):
    user_id = await db.get_user_id(session_id)
    if not session_id or not user_id:
        raise HTTPException(status_code=401, detail="no auth")

    perms = await ipc.request("check_perms", guild_id=guild_id, user_id=user_id)
    if not perms.response.get("perms"):
        return {"error": "You do not have access to this server"}

    update_guild_settings(guild_id, detection_status=bool(status))
    return RedirectResponse(url=f"/server/{guild_id}")

@app.get("/server/{guild_id}/settings/toggle_embed/{status}")
async def set_channel(guild_id: int, status: int, session_id: str = Cookie(None)):
    user_id = await db.get_user_id(session_id)
    if not session_id or not user_id:
        raise HTTPException(status_code=401, detail="no auth")

    perms = await ipc.request("check_perms", guild_id=guild_id, user_id=user_id)
    if not perms.response.get("perms"):
        return {"error": "You do not have access to this server"}

    update_guild_settings(guild_id, link_embed_status=bool(status))
    return RedirectResponse(url=f"/server/{guild_id}")

@app.get("/server/{guild_id}/settings/toggle_set/{set}/{status}")
async def set_channel(guild_id: int, set: str, status: int, session_id: str = Cookie(None)):
    user_id = await db.get_user_id(session_id)
    if not session_id or not user_id:
        raise HTTPException(status_code=401, detail="no auth")

    perms = await ipc.request("check_perms", guild_id=guild_id, user_id=user_id)
    if not perms.response.get("perms"):
        return {"error": "You do not have access to this server"}
    print(f"Set: {set}, Status: {status}")
    update_guild_settings(guild_id, **{set: bool(status)})
    return RedirectResponse(url=f"/server/{guild_id}")

@app.get("/logout")
async def logout(session_id: str = Cookie(None)):
    session = await db.get_session(session_id)
    if not session_id or not session:
        raise HTTPException(status_code=401, detail="no auth")

    token, _, _ = session

    response = RedirectResponse("/")
    response.delete_cookie(key="session_id", httponly=True)

    await db.delete_session(session_id)
    await api.revoke_token(token)

    return response


@app.exception_handler(404)
async def error_redirect(_, __):
    return RedirectResponse("/")


if __name__ == "__main__":
  #  uvicorn.run(app, host="0.0.0.0", port=8000)
    uvicorn.run(app, host="localhost", port=8000)
    # uvicorn.run("main:app", host="localhost", port=8000, reload=True)
