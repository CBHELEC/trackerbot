import country_emoji as ce
import giphy_client
import discord
import random
import requests
import asyncio
import owoencode
import owodecode
import re
import os
import numpy as np
from giphy_client.rest import ApiException
from functions import logs, eightball, google, general
from discord import app_commands
from bot import bot
from PIL import Image, ImageSequence
from io import BytesIO
from discord.app_commands import CheckFailure
from furrydb import *
from locationprofiledb import *

class Fun(app_commands.Group):
    """Fun Commands!"""
    def __init__(self, bot):
        super().__init__(name="fun", description="Fun Commands.")
        self.bot = bot
    
        self.context_menu = app_commands.ContextMenu(
            name="Decode OwO",
            callback=self.decode_owo,
            type=discord.AppCommandType.message
        )
        self.bot.tree.add_command(self.context_menu)

  #  async def interaction_check(self, interaction: discord.Interaction) -> bool:
   #     """Ensures commands in this group only run in a specific channel."""
    #    if interaction.channel.id == 1321995836464566435:
     #       await interaction.response.send_message("This command is not available in this channel.", ephemeral=True)
      #      return False
        
       # return True

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        """Only let commands run if the Server Owner or Admin has enabled them."""
        setting = get_guild_settings(interaction.guild.id)
        fun_status = int(setting.fun_set) if hasattr(setting, 'fun_set') else 1
        if fun_status == 0:
            raise CheckFailure("COMMANDS_DISABLED_BY_ADMIN")
        return True

    async def on_error(self, interaction: discord.Interaction, error: Exception) -> None:
        if isinstance(error, CheckFailure) and str(error) == "COMMANDS_DISABLED_BY_ADMIN":
            msg = "This command set has been disabled by the Server Owner or an Admin. Please contact them for more info."
            if not interaction.response.is_done():
                await interaction.response.send_message(msg, ephemeral=True)
            else:
                await interaction.followup.send(msg, ephemeral=True)
            return
        raise error
    
# DECODE_OWO CONTEXT
    async def decode_owo(self, interaction: discord.Interaction, message: discord.Message):
        """Decodes OwO text."""
        matches = re.findall(r'(?:[OoUuwW]+)', message.content)
        last_sequence = matches[-1] if matches else None
        await interaction.response.send_message(owodecode.decode(last_sequence), ephemeral=True)

# HELP
    @app_commands.command()
    async def help(self, interaction: discord.Interaction):
        """Shows all of the Fun commands."""
        embed = discord.Embed(title="Fun Commands",
                      colour=0xad7e66)
        embed.description = ("/fun 8ball <question> <potato_mode> - Asks the magic 8ball a question\n/fun avatar <user:optional> - Shows the avatar of a user\n/fun cat - Sends a random Cat image\n"
        "/fun coinflip - Flips a coin\n/fun define <word> - Sends the definition of a word\n/fun dog - Sends a random Dog image\n/fun google <query> - Search Google for web results\n"
        "/fun image <query> - Search Google for image results\n/fun math <expression> - Solves a math equation\n/fun roll <maxroll> - Rolls a random number\n/fun servericon - Send the server's icon\n"
        "/fun serverinfo - Shows some generic server info\n/fun userinfo <user:optional> - Shows some generic user info\n/fun petpet <user:optional> - Creates a PetPet gif for a user.\n"
        "/fun furry - Sends a random Furry gif :3\n/fun fakedoxx <user:optional> - Sends fake info about a user.\n/fun help - Shows all of the Fun commands")
        embed.set_footer(text="Help | Tracker",
                         icon_url="https://i.imgur.com/UrJoUHP.png")
        await interaction.response.send_message(embed=embed)
    
# ROLL
    @app_commands.command()
    @app_commands.describe(num="The maximum number you can roll.")
    async def roll(self, interaction: discord.Interaction, num: int):
        """Rolls a random number."""
        rollnum = random.randint(1, num)
        rng = discord.Embed(
            title=f"{interaction.user.name} rolled a {rollnum} (max = {num})",
            colour=0xad7e66)
        rng.set_footer(text="Roll | Tracker",
                 icon_url="https://i.imgur.com/UrJoUHP.png")
        await interaction.response.send_message(embed=rng)
        
# COINFLIP
    @app_commands.command()
    async def coinflip(self, interaction: discord.Interaction):
        """Flips a coin."""
        await interaction.response.defer()
        determine_flip = [1, 0]
        flipping = discord.Embed(title="A coin has been flipped...",
                                 colour=0xad7e66)
        flipping.set_image(url="https://i.imgur.com/nULLx1x.gif")
        flipping.set_footer(text="Coinflip | Tracker",
                 icon_url="https://i.imgur.com/UrJoUHP.png")
        msg = await interaction.followup.send(embed=flipping, content=None)
        await asyncio.sleep(3)
        if random.choice(determine_flip) == 1:
            heads = discord.Embed(title="The coin landed on heads!",
                                  colour=0xad7e66)
            heads.set_image(url="https://i.imgur.com/h1Os447.png")
            heads.set_footer(text="Coinflip | Tracker",
                 icon_url="https://i.imgur.com/UrJoUHP.png")
            await interaction.followup.edit_message(message_id=msg.id, embed=heads)
        else:
            tails = discord.Embed(title="The coin landed on tails!",
                                  colour=0xad7e66)
            tails.set_image(url="https://i.imgur.com/EiBLhPX.png")
            tails.set_footer(text="Coinflip | Tracker",
                 icon_url="https://i.imgur.com/UrJoUHP.png")
            await interaction.followup.edit_message(message_id=msg.id, embed=tails)
        
# MATH
    @app_commands.command()
    @app_commands.describe(expression="The math equation you want to solve.")
    async def math(self, interaction: discord.Interaction, expression: str):
        """Solves a math equation."""

        allowed_names = {k: v for k, v in np.__dict__.items() if not k.startswith("__")}
        allowed_names.update({"abs": abs, "round": round})

        try:
            result = eval(expression, {"__builtins__": {}}, allowed_names)

            def round_floats(x):
                if isinstance(x, float):
                    x = round(x, 2)
                    if x.is_integer():
                        return int(x)
                    return x
                if isinstance(x, (list, tuple, np.ndarray)):
                    return [round_floats(i) for i in x]
                return x

            result = round_floats(result)

            embed = discord.Embed(
                title=f"{general.escape_markdown(expression)} = {result}",
                colour=0xad7e66
            )
            embed.set_footer(
                text="Math | Tracker",
                icon_url="https://i.imgur.com/UrJoUHP.png"
            )
            await interaction.response.send_message(embed=embed)

        except ZeroDivisionError:
            embed = discord.Embed(
                title="<:denied:1336100920039313448> | Error! Division by zero is not allowed.",
                colour=0xad7e66
            )
            embed.set_footer(
                text="Math | Tracker",
                icon_url="https://i.imgur.com/UrJoUHP.png"
            )
            await interaction.response.send_message(embed=embed)

        except Exception:
            embed = discord.Embed(
                title="<:denied:1336100920039313448> | Error! Invalid expression - please use a valid math expression.",
                colour=0xad7e66
            )
            embed.set_footer(
                text="Math | Tracker",
                icon_url="https://i.imgur.com/UrJoUHP.png"
            )
            await interaction.response.send_message(embed=embed)

# 8ball
    @app_commands.command(name='8ball')
    @app_commands.choices(potato_mode=[
        app_commands.Choice(name="Enable", value="1"),
        app_commands.Choice(name="Disable (default)", value="2")
    ])
    @app_commands.describe(question="The question you would like to ask.", potato_mode="Whether you want to enable goof mode. Default = False.")
    async def eight_ball(self, interaction: discord.Interaction, *, question: str, potato_mode: app_commands.Choice[str] = None):
        """Asks the magic 8ball a question."""
        if potato_mode == None or potato_mode.value == "2":
            response = random.choice(eightball.eightball_answers) 
            embed = discord.Embed(title=f"{question}",
                        description=f"{response}", colour=0xad7e66)

            embed.set_footer(text="8ball | Tracker",
                    icon_url="https://i.imgur.com/UrJoUHP.png")
            await interaction.response.send_message(embed=embed)  
        else:
            response = random.choice(eightball.funny_eightball_answers) 
            embed = discord.Embed(title=f"<:potato:1341804459977605130> {question}",
                        description=f"{response}", colour=0xad7e66)

            embed.set_footer(text="8ball | Tracker",
                    icon_url="https://i.imgur.com/UrJoUHP.png")
            await interaction.response.send_message(embed=embed) 

# CAT
    @app_commands.command()
    async def cat(self, interaction: discord.Interaction):
        """Sends a random Cat image."""
        response = requests.get('https://api.thecatapi.com/v1/images/search')
        data = response.json()
        cat_image_url = data[0]['url']
        embed = discord.Embed(colour=0xad7e66)
        if random.randint(1, 100) <5: 
            embed.set_image(url="https://i.imgur.com/LU3AX1U.jpeg")
            embed.title = "<:wowza_cat:1378038803465371760> Wowza! A cat!"
        else:
            embed.set_image(url=f"{cat_image_url}")

        embed.set_footer(text="Cat | Tracker",
                 icon_url="https://i.imgur.com/UrJoUHP.png")
        await interaction.response.send_message(embed=embed)

# DOG
    @app_commands.command()
    async def dog(self, interaction: discord.Interaction):
        """Sends a random Dog image."""
        response = requests.get("https://random.dog/woof.json")
        data = response.json()
        dog_image_url = data["url"]
        embed = discord.Embed(colour=0xad7e66)

        embed.set_image(url=f"{dog_image_url}")

        embed.set_footer(text="Dog | Tracker",
                 icon_url="https://i.imgur.com/UrJoUHP.png")
        await interaction.response.send_message(embed=embed)

# GOOGLE
    @app_commands.command()
    @app_commands.describe(query="The query you want results for.")
    async def google(self, interaction: discord.Interaction, *, query: str):
        """Search Google for web results."""
        await interaction.response.defer()
        msg = await interaction.followup.send(f"<:search:1338134220718997625> | Searching for '{query}'. This may take a while!")
        msgid = msg.id
        results = google.google_search(query)
        if not results:
            return await interaction.followup.edit_message(message_id=msgid, content=f"<:denied:1336100920039313448> | No images found for '{query}'.")

        view = google.GoogleSearchView(results, query)
        embed = discord.Embed(
            title=results[0]['title'],
            url=results[0]['link'],
            description=results[0].get('snippet', ''),
            color=0xad7e66,
        )
        embed.set_footer(text=f"Result 1 / {len(results)} | {query} | Tracker", icon_url="https://i.imgur.com/kNe7FRh.png")
        await interaction.followup.edit_message(message_id=msgid, embed=embed, view=view, content=None)

# GOOGLE IMAGE
    @app_commands.command()
    @app_commands.describe(query="The query you want results for.")
    async def image(self, interaction: discord.Interaction, *, query: str):
        """Search Google for image results."""
        
        await interaction.response.defer()
        
        msg = await interaction.followup.send(f"<:search:1338134220718997625> | Image searching for '{query}'. This may take a while!")

        msgid = msg.id

        search_params = {
            'q': query,
            'num': 10,  # Number of results to fetch
            'safe': 'high',  # Ensures that results are safe for work (SFW)
            'fileType': 'png',  # Only JPG and PNG images
        }

        google.gis.search(search_params=search_params)
        
        images = [result.url for result in google.gis.results()] if google.gis.results() else []

        if images:
            view = google.ImageSearchView(images, query, timeout=300)
            view.msg = msg
            embed = discord.Embed(colour=0xad7e66)
            embed.set_footer(text=f"Image 1 / 15 | {query} | Tracker",
                 icon_url="https://i.imgur.com/kNe7FRh.png")
            embed.set_image(url=images[0])
            await interaction.followup.edit_message(message_id=msgid, embed=embed, view=view, content=None)
        else:
            await interaction.followup.edit_message(message_id=msgid, content=f"<:denied:1336100920039313448> | No images found for '{query}'.")

# SERVERINFO
    @app_commands.command()
    async def serverinfo(self, interaction: discord.Interaction):
        """Shows some generic server info."""
        server = interaction.guild
        creation_time = int(server.created_at.timestamp()) 
        embed = discord.Embed(title=f"Server Information for {server.name}", colour=0xad7e66)
        embed.description = (
            f"**Server Name**: {server.name}\n"
            f"**Server ID**: `{server.id}`\n"
            f"**Owner**: <@{server.owner_id}> ({server.owner_id})\n"
            f"**Member Count**: {server.member_count}\n"
            f"**Created At**: <t:{creation_time}:f>"
        )
        embed.set_thumbnail(url=server.icon.url)
        embed.set_footer(text="ServerInfo | Tracker",
            icon_url="https://i.imgur.com/UrJoUHP.png")
        await interaction.response.send_message(embed=embed)

# AVATAR
    @app_commands.command()
    @app_commands.describe(member="The member who's avatar you want to view.")
    async def avatar(self, interaction: discord.Interaction, member: discord.Member = None):
        """Shows the avatar of a user."""
        if member is None:
            member = interaction.user
        avatar_url = member.avatar.url if member.avatar else member.display_avatar.url
        embed = discord.Embed(title=f"{member.display_name}'s avatar:", colour=0xad7e66)

        embed.set_image(url=f"{avatar_url}")

        embed.set_footer(text="Avatar | Tracker",
                 icon_url="https://i.imgur.com/UrJoUHP.png")
        await interaction.response.send_message(embed=embed)

# SERVERICON
    @app_commands.command()
    async def servericon(self, interaction: discord.Interaction):
        """Send the server's icon."""
        server_icon = interaction.guild.icon.url 
        embed = discord.Embed(colour=0xad7e66)

        embed.set_image(url=f"{server_icon}")

        embed.set_footer(text="ServerIcon | Tracker",
                 icon_url="https://i.imgur.com/UrJoUHP.png")
        await interaction.response.send_message(embed=embed)

# USERINFO
    @app_commands.command()
    @app_commands.describe(member="The user you want info for.")
    async def userinfo(self, interaction: discord.Interaction, member: discord.Member = None):
        """Shows some generic user info."""
        if member is None:
            if isinstance(interaction.user, discord.Member):
                member = interaction.user
            else:
                member = await interaction.guild.fetch_member(interaction.user.id)

        roles = sorted(member.roles[1:], key=lambda role: role.position, reverse=True)
        displayed_roles = roles[:10]
        total_roles_count = len(roles)
        remaining_roles_count = total_roles_count - len(displayed_roles)
        roles_str = ' • '.join([f"<@&{role.id}>" for role in displayed_roles])
        if remaining_roles_count > 0:
            roles_str += f"\n... {remaining_roles_count} More"

        admin_permission = "✅" if member.guild_permissions.administrator else "❌"

        booster_status = "✅" if member.premium_since else "❌"

        username = member.name
        display_name = member.display_name

        if member.created_at is not None:
            created_at = f"<t:{int(member.created_at.timestamp())}:f> (<t:{int(member.created_at.timestamp())}:R>)"
        else:
            created_at = "Unknown"
        if member.joined_at is not None:
            joined_at = f"<t:{int(member.joined_at.timestamp())}:f> (<t:{int(member.joined_at.timestamp())}:R>)"
        else:
            joined_at = "Unknown"

        embed = discord.Embed(title=display_name, colour=0xad7e66)
        embed.set_author(name=f"{username}", icon_url=member.display_avatar.url)
        user = member if member else interaction.user
        avatar_url = user.avatar.url if user.avatar else user.display_avatar.url
        embed.set_thumbnail(url=avatar_url)

        embed.add_field(
            name="ℹ️ User Info",
            value=(
                f"User ID: `{member.id}` ({member.mention})\n"
                f"Created: {created_at}\n"
                f"Joined: {joined_at}\n"
                f"Administrator: {admin_permission}\n"
                f"Booster: {booster_status}"
            ),
            inline=False
        )
        embed.add_field(
            name=f"<:mention:1340087267678752860> {total_roles_count} Roles",
            value=f"{roles_str}",
            inline=False
        )

        embed.set_footer(text="UserInfo | Tracker",
            icon_url="https://i.imgur.com/UrJoUHP.png")

        await interaction.response.send_message(embed=embed)

# DICTIONARY
    @app_commands.command()
    @app_commands.describe(word="The word you want a definiton for.")
    async def define(self, interaction: discord.Interaction, *, word: str):
        """Sends the definition of a word."""
        url = f'https://api.dictionaryapi.dev/api/v2/entries/en/{word}'
        response = requests.get(url)

        if response.status_code == 200:
            data = response.json()
            if isinstance(data, list) and len(data) > 0:
                meaning = data[0]['meanings'][0]
                definition = meaning['definitions'][0]['definition']
                example = meaning['definitions'][0].get('example', 'No example available.')
                part_of_speech = meaning['partOfSpeech']

                embed = discord.Embed(title=f'Definition of {word}', colour=0xad7e66)
                embed.add_field(name='Part of Speech', value=part_of_speech, inline=False)
                embed.add_field(name='Definition', value=definition, inline=False)
                embed.add_field(name='Example', value=example, inline=False)

                embed.set_footer(text="Define | Tracker",
                 icon_url="https://i.imgur.com/UrJoUHP.png")

                await interaction.response.send_message(embed=embed)
            else:
                await interaction.response.send_message(f'No definitions found for "{word}".')
        else:
            await interaction.response.send_message(f'Error: Could not retrieve definitions for "{word}".')

# PETPET
    @app_commands.command()
    @app_commands.describe(user="The user you want to petpet.")
    async def petpet(self, interaction: discord.Interaction, user: discord.User = None):
        """Petpets a user."""
        await interaction.response.defer()
        user = user or interaction.user
        avatar_url = user.avatar.url if user.avatar else user.display_avatar.url
        api_url = f"https://api.obamabot.me/v2/image/petpet?image={avatar_url}"
        
        response = requests.get(api_url)
        if response.status_code != 200:
            await logs.log_error(interaction.guild, bot, interaction.command.name, "Failed to generate petpet GIF. The API may be down.")
            return
        
        gif_url = response.json().get("url")
        if not gif_url:
            await logs.log_error(interaction.guild, bot, interaction.command.name, "Failed to retrieve petpet GIF. API response was invalid.")
            return
        
        gif_response = requests.get(gif_url)
        if gif_response.status_code != 200:
            await logs.log_error(interaction.guild, bot, interaction.command.name, "Failed to download the GIF.")
            return
        
        gif_image = Image.open(BytesIO(gif_response.content))
        frames = [
            frame.copy().resize((frame.width * 2, frame.height * 2), Image.Resampling.LANCZOS)
            for frame in ImageSequence.Iterator(gif_image)
        ]

        gif_bytes = BytesIO()
        frames[0].save(
            gif_bytes, format="GIF", save_all=True, append_images=frames[1:], loop=0, duration=gif_image.info["duration"]
        )
        gif_bytes.seek(0)

        file = discord.File(gif_bytes, filename="petpet_large.gif")
        await interaction.followup.send(f"{interaction.user.mention} pets {user.mention}! <:pet:1350528870830571621><a:heart:1350529555965677710>", file=file)

# FURRY
    @app_commands.command()
    @app_commands.choices(type=[
        app_commands.Choice(name="Image", value="1"),
        app_commands.Choice(name="GIF", value="2")
    ])
    @app_commands.describe(type="The type of Furry content you want.")
    async def furry(self, interaction: discord.Interaction, type: app_commands.Choice[str]):
        """Sends a random Furry image or gif."""
        if type.value == "1":
            response = requests.get(url="http://sheri.bot/api/mur/").json()

            user_id = str(interaction.user.id)
            current, best, message = update_furry_streak(user_id, response['url'])
            
            embed = discord.Embed(title=f"Woof!", url=response['source'], colour=0xad7e66)

            embed.add_field(name="Inappropriate Image?",
                            value=f"[Report it here by clicking this link.]({response['report_url']})")
            embed.set_image(url=response['url'])

            embed.set_footer(text="Furry | Tracker | Sheri API",
                 icon_url="https://i.imgur.com/UrJoUHP.png")

            if message:
                await interaction.followup.send(message, ephemeral=False)

            await interaction.response.send_message(embeds=[embed])
        elif type.value == "2":
            api_instance = giphy_client.DefaultApi()
            api_key = os.getenv('GIPHY_API_KEY')
            tag = 'fursuit'
            try:
                while True:
                    api_response = api_instance.gifs_random_get(api_key, tag=tag)
                    blacklist = ["https://giphy.com/gifs/motion-capture-abillmiller-a-bill-miller-ch1cijjnCVK2T656w1"]
                    if api_response.data.url not in blacklist:
                        await interaction.response.send_message(api_response.data.url)
                        break
            except ApiException as e:
                await logs.log_error(interaction.guild, bot, interaction.command.name, f"Failed to retrieve GIF from Giphy API. Error: {e}")
        else:
            await interaction.response.send_message("Invalid type selected. Please choose either 'Image' or 'GIF'.")

# FAKEDOXX
    @app_commands.command(name="fakedoxx")
    async def fake_dox(self, interaction: discord.Interaction, member: discord.Member = None):
        """Generate fake information for a user."""
        member = member if member else interaction.user

        fake_ip = ".".join(str(random.randint(1, 255)) for _ in range(4))

        fake_countries = [
            "Afghanistan", "Albania", "Algeria", "Andorra", "Angola", "Antigua and Barbuda", "Argentina", "Armenia", "Australia", "Austria", "Azerbaijan", "Bahamas", "Bahrain", "Bangladesh", "Barbados", "Belarus", "Belgium", "Belize", "Benin", "Bhutan", "Bolivia", "Bosnia and Herzegovina", "Botswana", "Brazil", "Brunei", "Bulgaria", "Burkina Faso", "Burundi", "Cabo Verde", "Cambodia", "Cameroon", "Canada", "Central African Republic", "Chad", "Chile", "China", "Colombia", "Comoros", "Congo", "Costa Rica", "Croatia", "Cuba", "Cyprus", "Czech Republic", "Democratic Republic of the Congo", "Denmark", "Djibouti", "Dominica", "Dominican Republic", "Ecuador", "Egypt", "El Salvador", "Equatorial Guinea", "Eritrea", "Estonia", "Eswatini", "Ethiopia", "Fiji", "Finland", "France", "Gabon", "Gambia", "Georgia", "Germany", "Ghana", "Greece", "Grenada", "Guatemala", "Guinea", "Guinea-Bissau", "Guyana", "Haiti", "Honduras", "Hungary", "Iceland", "India", "Indonesia", "Iran", "Iraq", "Ireland", "Israel", "Italy", "Ivory Coast", "Jamaica", "Japan", "Jordan", "Kazakhstan", "Kenya", "Kiribati", "Korea (North)", "Korea (South)", "Kuwait", "Kyrgyzstan", "Laos", "Latvia", "Lebanon", "Lesotho", "Liberia", "Libya", "Liechtenstein", "Lithuania", "Luxembourg", "Madagascar", "Malawi", "Malaysia", "Maldives", "Mali", "Malta", "Marshall Islands", "Mauritania", "Mauritius", "Mexico", "Micronesia", "Moldova", "Monaco", "Mongolia", "Montenegro", "Morocco", "Mozambique", "Myanmar", "Namibia", "Nauru", "Nepal", "Netherlands", "New Zealand", "Nicaragua", "Niger", "Nigeria", "North Macedonia", "Norway", "Oman", "Pakistan", "Palau", "Panama", "Papua New Guinea", "Paraguay", "Peru", "Philippines", "Poland", "Portugal", "Qatar", "Romania", "Russia", "Rwanda", "Saint Kitts and Nevis", "Saint Lucia", "Saint Vincent and the Grenadines", "Samoa", "San Marino", "Sao Tome and Principe", "Saudi Arabia", "Senegal", "Serbia", "Seychelles", "Sierra Leone", "Singapore", "Slovakia", "Slovenia", "Solomon Islands", "Somalia", "South Africa", "South Sudan", "Spain", "Sri Lanka", "Sudan", "Suriname", "Sweden", "Switzerland", "Syria", "Taiwan", "Tajikistan", "Tanzania", "Thailand", "Timor-Leste", "Togo", "Tonga", "Trinidad and Tobago", "Tunisia", "Turkey", "Turkmenistan", "Tuvalu", "Uganda", "Ukraine", "United Arab Emirates", "United Kingdom", "United States", "Uruguay", "Uzbekistan", "Vanuatu", "Vatican City", "Venezuela", "Vietnam", "Yemen", "Zambia", "Zimbabwe"
        ]
        fake_country = random.choice(fake_countries)

        embed = discord.Embed(
            title=f"DOXXED {member.name}",
            description=f"**IP Address:** `{fake_ip}`\n**Location:** `{fake_country}`",
            color=0xad7e66
        )
        embed.set_thumbnail(url=member.display_avatar.url)
        embed.set_footer(text="FakeDoxx | Tracker",
                 icon_url="https://i.imgur.com/UrJoUHP.png")
        embed.set_author(name="THIS IS A JOKE, AND NOT REAL.")

        await interaction.response.send_message(embed=embed)

# OWO_ENCODE
    @app_commands.command()
    @app_commands.describe(text="The text you want to encode.")
    async def owo_encode(self, interaction: discord.Interaction, text: str):
        """Encodes text to OwO."""
        channel = interaction.channel
        await channel.send(f"{interaction.user.mention} OwOs: {owoencode.encode(text)}")
        await interaction.response.send_message("OwO!", ephemeral=True)

# OWO_DECODE
    @app_commands.command()
    @app_commands.describe(text="The text you want to decode.")
    async def owo_decode(self, interaction: discord.Interaction, text: str):
        """Decodes OwO text."""
        matches = re.findall(r'(?:[OoUuwW]+)', text)
        last_sequence = matches[-1] if matches else None
        await interaction.response.send_message(owodecode.decode(last_sequence), ephemeral=True)

# LOCATIONPROFILE
    @app_commands.command()
    async def locationprofile(self, interaction: discord.Interaction, user: discord.User = None):
        """Shows your or a users location profile, or creates one."""
        enduser = user or interaction.user
        profile = get_user_profile(enduser.id)

        if not profile:
            if user:
                await interaction.response.send_message(f"{user.mention} doesn't have a location profile yet. Maybe you should prompt them to make one?", ephemeral=True)
            else:
                await interaction.response.send_message("You don't have a location profile yet. Press the button below to make one.", ephemeral=True, view=CreateButton(self.bot, interaction))
            return

        embed = discord.Embed(title=f"{enduser.display_name}'s Location Profile", colour=0xad7e66)
        embed.add_field(name="Location", value=ce.flag(profile.country) + " " + profile.country or "Not set", inline=False)
        embed.add_field(name="Timezone", value=f"{profile.timezone} (<t:{int(time_in_tz(profile.timezone).timestamp())}:T>)" or "Not set", inline=False)

        embed.set_footer(text="LocationProfile | Tracker",
                 icon_url="https://i.imgur.com/UrJoUHP.png")

        await interaction.response.send_message(embed=embed, ephemeral=True)

async def setup(bot):
    bot.tree.add_command(Fun(bot))