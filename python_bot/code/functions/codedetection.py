import json
import pycaching
import re
from collections.abc import Iterable
from functions import static_var
from database import *

GC_BLACKLIST = ["GC", "GCHQ", "GCFAQ", "GCC"]
TL_BLACKLIST = ["TL"]
GL_BLACKLIST = ["GL"]
PR_BLACKLIST = ["PR"]
TB_BLACKLIST = ["TB", "TBF", "TBH", "TBS", "TBDISCOVER", "TBDROP", "TBGRAB", "TBMISSING", "TBRETRIEVE", "TBVISIT"]
GT_BLACKLIST = ["GT"]

INVITE_REGEX = re.compile(
    r'(https?:\/\/)?(www\.)?(discord\.gg|discord\.com\/invite)\/([A-Za-z0-9-]+)',
    re.IGNORECASE
)

def redact_discord_invites(text: str) -> str:
    return INVITE_REGEX.sub(
        lambda m: f"https​:/​/​discord​.gg​/rеdаctеd",
        text
    )

with (static_var.DATA_DIR / 'name-icon.json').open("r", encoding="utf-8") as file:
    emoji_names: dict[str, dict[str, str]] = json.load(file)

def get_emoji_from_name(emoji_name: str) -> str:
    global emoji_names
    return emoji_names.get(emoji_name, {}).get("emoji", "")

def find_gc_tb_codes(s: str) -> tuple[bool, list[str], list[str]]:
    gc_matches = re.findall(r'(?<!:)\b(GC[A-Z0-9]{1,5})(?:\b|_)', s, re.IGNORECASE)
    tb_matches = re.findall(r'(?<!:)\b(TB[A-Z0-9]{1,5})(?:\b|_)', s, re.IGNORECASE)

    gc_codes = []
    for item in gc_matches:
        code = item.upper()
        if code not in GC_BLACKLIST and code not in gc_codes:
            gc_codes.append(code)

    tb_codes = []
    for item in tb_matches:
        code = item.upper()
        if code not in TB_BLACKLIST and code not in tb_codes:
            tb_codes.append(code)

    if not gc_codes and not tb_codes:
        return False, [], []

    return True, gc_codes, tb_codes

async def find_pr_codes(s: str) -> list[str]:
    pr_matches: list[str] = re.findall(r'(?<!:)\b(PR[A-Z0-9]{1,5})(?:\b|_)', s, re.IGNORECASE)

    pr_codes = []
    for item in pr_matches:
        code = item.upper()
        if code not in PR_BLACKLIST and code not in pr_codes:
            pr_codes.append(code)

    return pr_codes

async def find_gt_codes(s: str) -> list[str]:
    gt_matches: list[str] = re.findall(r'(?<!:)\b(GT[A-Z0-9]{1,3})(?:\b|_)', s, re.IGNORECASE)

    gt_codes = []
    for item in gt_matches:
        code = item.upper()
        if code not in GT_BLACKLIST and code not in gt_codes:
            gt_codes.append(code)

    return gt_codes

async def find_gl_tl_codes(s: str) -> tuple[list[str], list[str]]:
    gl_matches: list[str] = re.findall(r'\bGL[A-Za-z0-9]{1,9}\b', s, re.IGNORECASE)
    tl_matches: list[str] = re.findall(r'\bTL[A-Za-z0-9]{1,9}\b', s, re.IGNORECASE)

    gl_codes = []
    for item in gl_matches:
        code = item.upper()
        if code not in GL_BLACKLIST and code not in gl_codes:
            gl_codes.append(code)

    tl_codes = []
    for item in tl_matches:
        code = item.upper()
        if code not in TL_BLACKLIST and code not in tl_codes:
            tl_codes.append(code)

    return gl_codes, tl_codes



g_obj = pycaching.login(static_var.GEOCACHING_USERNAME, static_var.GEOCACHING_PASSWORD)

async def get_gt_code_info(gt_codes: Iterable[str] | str, guild_id: int):
    messages = []
    if isinstance(gt_codes, str):
        gt_codes = [gt_codes]

    serverinfo = get_guild_settings(guild_id)
    cd_limit = serverinfo.code_detection_limit
    
    extra_codes = len(gt_codes) - cd_limit
    if extra_codes > 0:
        messages.append(f"**(... {extra_codes} truncated)**")

    for code in gt_codes[:cd_limit]:
        try:
            gt = g_obj.get_geotour(code)
            name = gt['name']
            fp_count = gt['fp_count']
            location_name = gt['location_name']
            messages.append(f"<:geotour:1457794800714514707> {name} | 🩵 {fp_count} |📍 {location_name}")
        except Exception as e:
            print(e)
            messages.append(f"<:DNF:1368989100220092516> **That GeoTour doesn't exist!**")

    return "\n".join(messages)  

async def get_gl_tl_code_info(gl_codes: Iterable[str], tl_codes: Iterable[str], guild_id: int):
    messages = []

    serverinfo = get_guild_settings(guild_id)
    cd_limit = serverinfo.code_detection_limit
    
    extra_codes = len(gl_codes) + len(tl_codes) - cd_limit
    if extra_codes > 0:
        messages.append(f"**(... {extra_codes} truncated)**")

    for code, code_type in [(c, "GL") for c in list(gl_codes)[:cd_limit]] + [(c, "TL") for c in list(tl_codes)[:cd_limit]]:
        try:
            log = g_obj.get_log(code)

            author = log.author or "Unknown"
            logtype = log.type.name if log.type else "Unknown"
            raw_date = log.visited if log.visited else "Unknown"
            text = log.text or "Unknown"
            cachecode = log.geocache_code if log.geocache_code else log.trackable_code
            
            if isinstance(raw_date, (datetime, date)):
                dt = raw_date if isinstance(raw_date, datetime) else datetime.combine(raw_date, datetime.min.time())
                timestamp = int(dt.timestamp())
                time_display = f"<t:{timestamp}:R>"
            elif isinstance(raw_date, str) and raw_date != "Unknown":
                try:
                    dt = datetime.strptime(raw_date, "%Y-%m-%dT%H:%M:%S")
                except ValueError:
                    try:
                        dt = datetime.strptime(raw_date, "%Y-%m-%d")
                    except ValueError:
                        dt = None
                
                if dt:
                    timestamp = int(dt.timestamp())
                    time_display = f"<t:{timestamp}:R>"
                else:
                    time_display = "Unknown date"
            else:
                time_display = "Unknown date"

            logtype_map = {
                "discovered_it": "<:TBDiscover:1369015617176207421>",
                "announcement": "📢",
                "archive": "<:Archive:1369015619231420497>",
                "attended": "<:Attended:1369015554257719334>",
                "didnt_find_it": "<:DNF:1368989100220092516>",
                "enable_listing": "<:Enabled:1369010377815494708>",
                "found_it": "<:Found:1368989281909215302>",
                "grabbed_it": "<:TBGrab:1369015569151430687>",
                "marked_missing": "<:TBMissing:1369015565171298335>",
                "needs_archive": "<:NeedsArchive:1369015557323755730>",
                "needs_maintenance": "<:NeedsMaintenence:1369010381774651504>",
                "note": "<:WriteNote:1369010379815911565>",
                "oc_team_comment": "💬",
                "owner_maintenance": "<:OwnerMaintenence:1369010374631751832>",
                "placed_it": "<:TBDrop:1369015563388584017>",
                "post_reviewer_note": "<:ReviewerNote:1369015567062667404>",
                "publish_listing": "<:Upload:1369010376662056970>",
                "retract": "<:ReviewerDeny:1369015615561666560>",
                "retrieved_it": "<:TBRetrieve:1369015561660399620>",
                "submit_for_review": "<:ReviewerNote:1369015567062667404>",
                "temp_disable_listing": "<:Disabled:1369009017552371902>",
                "unarchive": "<:Unarchive:1369015555570270409>",
                "update_coordinates": "<:Relocate:1369015572183908462>",
                "visit": "<:TBVisit:1369016734161309706>",
                "webcam_photo_taken": "<:LogImage:1369015560662417500>",
                "will_attend": "<:WillAttend:1369015558909071411>"
            }

            logtype_display = logtype_map.get(logtype, logtype)

            messages.append(
                f"[{code}](<https://coord.info/{code}>) - {logtype_display} | {author}\n"
                f"🗓️ {time_display} | [{cachecode}](<https://coord.info/{cachecode}>)\n"
                f"Log Contents: {redact_discord_invites(text)}"
            )

        except Exception as e:
            print(e)
            return

    return "\n\n".join(messages)

async def get_pr_code_info(pr_codes: Iterable[str] | str, bot, guild_id: int):
    messages = []
    if isinstance(pr_codes, str):
        pr_codes = [pr_codes]

    if guild_id:
        serverinfo = get_guild_settings(guild_id)
        cd_limit = serverinfo.code_detection_limit
    else:
        cd_limit = 3

    extra_codes = len(pr_codes) - cd_limit
    if extra_codes > 0:
        messages.append(f"**(... {extra_codes} truncated)**")

    for code in pr_codes[:cd_limit]:
        try:
            try:
                profile = g_obj.get_user(pr_code=code)
            except AttributeError as e:
                g_obj.logout()
                g_obj.login(static_var.GEOCACHING_USERNAME, static_var.GEOCACHING_PASSWORD)
                profile = g_obj.get_user(pr_code=code) 
            except Exception as e:
                raise e

            name = profile.name
            joined_date = profile.joined_date
            location = profile.location
            profile_picture_url = profile.profile_picture_url
            membership_status = profile.membership_status
            favorite_points_received = profile.favorite_points_received
            finds_count = profile.found_count
            hides_count = profile.hidden_count
            last_visited_date = profile.last_visited_date

            joined_ts = int(datetime.combine(joined_date, time.min).timestamp())
            last_visited_ts = int(datetime.combine(last_visited_date, time.min).timestamp())

            emoji_guild = bot.get_guild(int(os.getenv("EMOJI_GUILD_ID")) if os.getenv("EMOJI_GUILD_ID") else None)
            emoji = None
            if emoji_guild:
                emojiname = name.translate(str.maketrans('', '', string.punctuation))
                emoji2 = await emoji_guild.create_custom_emoji(name=f"PR_{emojiname}", image=requests.get(profile_picture_url).content)
                emoji = await emoji_guild.fetch_emoji(emoji2.id)

            pmo = "<:Premium:1368989525405335552>" if str(membership_status) == "MembershipStatus.premium" else ""
            emoji_str = f"<:{emoji.name}:{emoji.id}>" if emoji else f"👤"

            finalmessage = f"""<:user:1453018988362731601> {code} | {pmo} {emoji_str} [{name}](<https://geocaching.com/p/?u={name}>)
<:join:1453020390803898438> <t:{joined_ts}:R> | 🛂 <t:{last_visited_ts}:R>
📍 {location} | <:Found:1368989281909215302> {finds_count} | <:OwnedCache:1368989502281875536> {hides_count} | 🩵 {favorite_points_received}"""
            
            if emoji:
                async def delete_emoji_later():
                    await asyncio.sleep(60)
                    try:
                        await emoji.delete()
                    except:
                        pass 
                asyncio.create_task(delete_emoji_later())

            messages.append(finalmessage)

        except Exception as e:
            print(e)
            return
    
    return "\n\n".join(messages)

async def get_username_pr_info(usernames: str, bot):
    messages = []
    try:
        try:
            profile = g_obj.get_user(name=usernames)
            profile.load()
        except AttributeError as e:
            g_obj.logout()
            g_obj.login(static_var.GEOCACHING_USERNAME, static_var.GEOCACHING_PASSWORD)
            profile = g_obj.get_user(name=usernames)
            profile.load()
        except Exception as e:
            raise e
            
        name = profile.name
        pr_code = profile.pr_code
        joined_date = profile.joined_date
        location = profile.location
        profile_picture_url = profile.profile_picture_url
        membership_status = profile.membership_status
        favorite_points_received = profile.favorite_points_received
        finds_count = profile.found_count
        hides_count = profile.hidden_count
        last_visited_date = profile.last_visited_date
        joined_ts = int(datetime.combine(joined_date, time.min).timestamp())
        last_visited_ts = int(datetime.combine(last_visited_date, time.min).timestamp())
        emoji_guild = bot.get_guild(int(os.getenv("EMOJI_GUILD_ID")) if os.getenv("EMOJI_GUILD_ID") else None)
        emoji = None
        if emoji_guild:
            emojiname = name.translate(str.maketrans('', '', string.punctuation))
            emoji2 = await emoji_guild.create_custom_emoji(name=f"PR_{emojiname}", image=requests.get(profile_picture_url).content)
            emoji = await emoji_guild.fetch_emoji(emoji2.id)
        pmo = "<:Premium:1368989525405335552>" if str(membership_status) == "MembershipStatus.premium" else ""
        emoji_str = f"<:{emoji.name}:{emoji.id}>" if emoji else f"👤"
        finalmessage = f"""<:user:1453018988362731601> {pr_code} | {pmo} {emoji_str} [{name}](<https://geocaching.com/p/?u={name}>)
<:join:1453020390803898438> <t:{joined_ts}:R> | 🛂 <t:{last_visited_ts}:R>
📍 {location} | <:Found:1368989281909215302> {finds_count} | <:OwnedCache:1368989502281875536> {hides_count} | 🩵 {favorite_points_received}"""
            
        messages.append(finalmessage)
        
        if emoji:
            async def delete_emoji_later():
                await asyncio.sleep(60)
                try:
                    await emoji.delete()
                except:
                    pass 
            asyncio.create_task(delete_emoji_later())
    except Exception as e:
        return
    
    return "\n\n".join(messages)

def get_cache_basic_info(guild_id: int, geocache_codes: Iterable[str]=[], tb_codes: Iterable[str]=[]):
    deadcode = False
    global g_obj
    final_message = []
    
    if guild_id:
        serverinfo = get_guild_settings(guild_id)
        cd_limit = serverinfo.code_detection_limit
    else:
        cd_limit = 3
    extra_caches = len(geocache_codes) - cd_limit

    for code in geocache_codes[:cd_limit]:
        try:
            try:
                cache = g_obj.get_cache(code)
                cache.load_quick()
            except AttributeError as e:
                g_obj.logout()
                g_obj.login(static_var.GEOCACHING_USERNAME, static_var.GEOCACHING_PASSWORD)

                cache = g_obj.get_cache(code)
                cache.load_quick()
            except Exception as e:
                raise e

            name = cache.name
            size = cache.size
            fps = cache.favorites
            difficulty = cache.difficulty
            terrain = cache.terrain
            author = cache.author
            pmo = cache.pm_only
            cache_type = cache.type
            status = cache.status

            if status == 0:
                prefix = ""
            elif status == 1:
                prefix = "<:Disabled:1369009017552371902>"
            elif status == 2:
                prefix = "<:Archive:1369015619231420497>"
            elif status == 3:
                raise Exception(f"found an unpublished cache: {code}")
            elif status == 4:
                prefix = ":lock:"

            emoji_name = f"{cache_type.name if cache_type.name != 'lost_and_found_event' else 'community_celebration'}"
            emoji_text = f"{prefix}{get_emoji_from_name(emoji_name)}"

            final_message.append(f"""{'<:Premium:1368989525405335552>' if pmo else ''}{emoji_text} [{code}](<https://coord.info/{code}>) - {name} | {author}
:light_blue_heart: {fps} | :mag_right: D{difficulty} - T{terrain} :mountain_snow: | <:tub:1327698135710957609> {size.value.capitalize()}""")

        except Exception as e:
            if guild_id == 0:
                final_message.append(f"<:DNF:1368989100220092516> **That Geocache doesn't exist!**")
            else:
                gsettings = get_guild_settings(guild_id)
                if gsettings.deadcode == 1:
                    final_message.append(f"<:DNF:1368989100220092516> **That Geocache doesn't exist!**")
                else:
                    deadcode = True
                    return final_message, deadcode

    for trackable in tb_codes[:3]:
        try:
            tb = g_obj.get_trackable(trackable)
            tb.load()

            name = tb.name
            owner = tb.owner

            final_message.append(
                f"""<:TravelBug:1368989710818480169> [{trackable}](<https://coord.info/{trackable}>) - {name} | {owner}"""
            )

        except Exception as e:
            if guild_id == 0:
                final_message.append(f"<:DNF:1368989100220092516> **That Trackable doesn't exist!**")
            else:
                gsettings = get_guild_settings(guild_id)
                if gsettings.deadcode == 1:
                    final_message.append(f"<:DNF:1368989100220092516> **That Trackable doesn't exist!**")
                else:
                    deadcode = True
                    return final_message, deadcode

    extra_caches = len(geocache_codes) - cd_limit
    if extra_caches > 0:
        final_message.append(f"**(... {extra_caches} truncated)**")

    extra_tbs = len(tb_codes) - cd_limit
    if extra_tbs > 0:
        final_message.append(f"**(... {extra_tbs} truncated)**")

    final_message = "\n".join(final_message)
    return final_message, deadcode

async def split_message(msg, content, cd_split_status=True):
    limit = 1990
    if len(content) <= limit:
        await msg.reply(content)
        return

    if not cd_split_status:
        await msg.reply(content[:limit-3] + "...")
        return

    first_chunk = True
    while content:
        if len(content) <= limit:
            split_at = len(content)
        else:
            split_at = content.rfind('\n', 0, limit)
            if split_at == -1:
                split_at = content.rfind(' ', 0, limit)
                if split_at == -1:
                    split_at = limit

        chunk = content[:split_at].rstrip('\n ').rstrip()
        
        if chunk:
            if first_chunk:
                await msg.reply(chunk)
                first_chunk = False
            else:
                await msg.channel.send(chunk)

        content = content[split_at:].lstrip('\n ').rstrip()    