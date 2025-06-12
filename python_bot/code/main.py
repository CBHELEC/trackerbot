import os
import discord
import ezcord
import uvicorn
from discord.ext.ipc import Client
from fastapi import Cookie, FastAPI, HTTPException, Request, Body
from fastapi.responses import RedirectResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from starlette.templating import Jinja2Templates
from contextlib import asynccontextmanager
from backend import DiscordAuth, db, feature_db
from database import *
from datetime import datetime

from dotenv import load_dotenv
load_dotenv(".env")
CLIENT_ID = os.getenv('CLIENT_ID')
CLIENT_SECRET = os.getenv('CLIENT_SECRET')
REDIRECT_URI = os.getenv('REDIRECT_URI')
SECRET_KEY = os.getenv('SECRET_KEY')

LOGIN_URL = f"https://discord.com/oauth2/authorize?client_id={CLIENT_ID}&response_type=code&redirect_uri=http%3A%2F%2Flocalhost%3A8000%2Fcallback&scope=identify+guilds"
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
    uvicorn.run(app, host="localhost", port=8000)
    # uvicorn.run("main:app", host="localhost", port=8000, reload=True)
