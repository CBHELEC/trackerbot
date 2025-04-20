import giphy_client
from giphy_client.rest import ApiException
from functions import *
import discord
from discord import app_commands
import random
import requests
import asyncio
from datetime import datetime, timezone
from bot import bot
from PIL import Image, ImageSequence
from io import BytesIO
from sympy import sympify, SympifyError

class Fun(app_commands.Group):
    """Fun Commands!"""
    
  #  async def interaction_check(self, interaction: discord.Interaction) -> bool:
   #     """Ensures commands in this group only run in a specific channel."""
    #    if interaction.channel.id == 1321995836464566435:
     #       await interaction.response.send_message("This command is not available in this channel.", ephemeral=True)
      #      return False
        
       # return True
    
# HELP
    @app_commands.command()
    async def help(self, interaction: discord.Interaction):
        """Shows all of the Fun commands."""
        embed = discord.Embed(title="Fun Commands",
                      colour=0xad7e66)

        embed.add_field(name="",
                value="/fun 8ball <question> <potato_mode> - Asks the magic 8ball a question\n/fun avatar <user> - Shows the avatar of a user\n/fun cat - Sends a random Cat image\n/fun coinflip - Flips a coin\n/fun define <word> - Sends the definition of a word\n/fun dog - Sends a random Dog image\n/fun google <query> - Search Google for web results\n/fun image <query> - Search Google for image results\n/fun math <expression> - Solves a math equation\n/fun roll <maxroll> - Rolls a random number\n/fun servericon - Send the server's icon\n/fun serverinfo - Shows some generic server info\n/fun userinfo <user> - Shows some generic user info\n/fun petpet <user> - Creates a PetPet gif for a user.\n/fun furry - Sends a random Furry gif :3\n/fun help - Shows all of the Fun commands",
                inline=False)
        embed.set_footer(text="Help | Tracker",
                         icon_url="https://i.imgur.com/J8jXkhj.png")
        await interaction.response.send_message(embed=embed)
    
# ROLL
    @app_commands.command()
    @app_commands.describe(num="The maximum number you can roll.")
    async def roll(self, interaction: discord.Interaction, num: int):
        """Rolls a random number."""
        rollnum = random.randint(1, num)
        rng = discord.Embed(
            title=f"{interaction.user.mention} ({interaction.user.name}) rolled a {rollnum} (max = {num})",
            colour=0xad7e66)
        rng.set_footer(text="Roll | Tracker",
                 icon_url="https://i.imgur.com/J8jXkhj.png")
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
                 icon_url="https://i.imgur.com/J8jXkhj.png")
        msg = await interaction.followup.send(embed=flipping, content=None)
        await asyncio.sleep(3)
        if random.choice(determine_flip) == 1:
            heads = discord.Embed(title="The coin landed on heads!",
                                  colour=0xad7e66)
            heads.set_image(url="https://i.imgur.com/h1Os447.png")
            heads.set_footer(text="Coinflip | Tracker",
                 icon_url="https://i.imgur.com/J8jXkhj.png")
            await interaction.followup.edit_message(message_id=msg.id, embed=heads)
        else:
            tails = discord.Embed(title="The coin landed on tails!",
                                  colour=0xad7e66)
            tails.set_image(url="https://i.imgur.com/EiBLhPX.png")
            tails.set_footer(text="Coinflip | Tracker",
                 icon_url="https://i.imgur.com/J8jXkhj.png")
            await interaction.followup.edit_message(message_id=msg.id, embed=tails)
        
# MATH
    @app_commands.command()
    @app_commands.describe(expression="The math equation you want to solve.")
    async def math(self, interaction: discord.Interaction, expression: str):
        """Solves a math equation."""
        try:
            result = sympify(expression)
            embed = discord.Embed(
                title=f"{escape_markdown(expression)} = {result}",
                colour=0xad7e66
            )
            embed.set_footer(
                text="Math | Tracker",
                icon_url="https://i.imgur.com/J8jXkhj.png"
            )
            await interaction.response.send_message(embed=embed)
        except SympifyError:
            embed = discord.Embed(
                title="<:denied:1336100920039313448> | Error! Invalid expression - please use a valid math expression.",
                colour=0xad7e66
            )
            embed.set_footer(
                text="Math | Tracker",
                icon_url="https://i.imgur.com/J8jXkhj.png"
            )
            await interaction.response.send_message(embed=embed)
        except ZeroDivisionError:
            embed = discord.Embed(
                title="<:denied:1336100920039313448> | Error! Division by zero is not allowed.",
                colour=0xad7e66
            )
            embed.set_footer(
                text="Math | Tracker",
                icon_url="https://i.imgur.com/J8jXkhj.png"
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
            response = random.choice(eightball_answers) 
            embed = discord.Embed(title=f"{question}",
                        description=f"{response}", colour=0xad7e66)

            embed.set_footer(text="8ball | Tracker",
                    icon_url="https://i.imgur.com/J8jXkhj.png")
            await interaction.response.send_message(embed=embed)  
        else:
            response = random.choice(funny_eightball_answers) 
            embed = discord.Embed(title=f"<:potato:1341804459977605130> {question}",
                        description=f"{response}", colour=0xad7e66)

            embed.set_footer(text="8ball | Tracker",
                    icon_url="https://i.imgur.com/J8jXkhj.png")
            await interaction.response.send_message(embed=embed) 

# CAT
    @app_commands.command()
    async def cat(self, interaction: discord.Interaction):
        """Sends a random Cat image."""
        response = requests.get('https://api.thecatapi.com/v1/images/search')
        data = response.json()
        cat_image_url = data[0]['url']
        embed = discord.Embed(colour=0xad7e66)

        embed.set_image(url=f"{cat_image_url}")

        embed.set_footer(text="Cat | Tracker",
                 icon_url="https://i.imgur.com/J8jXkhj.png")
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
                 icon_url="https://i.imgur.com/J8jXkhj.png")
        await interaction.response.send_message(embed=embed)

# GOOGLE
    @app_commands.command()
    @app_commands.describe(query="The query you want results for.")
    async def google(self, interaction: discord.Interaction, *, query: str):
        """Search Google for web results."""
        await interaction.response.defer()
        msg = await interaction.followup.send(f"<:search:1338134220718997625> | Searching for '{query}'. This may take a while. <:happy_tracker:1329914691656614042>")
        msgid = msg.id
        results = google_search(query)
        if not results:
            return await interaction.followup.edit_message(message_id=msgid, content=f"<:denied:1336100920039313448> | No images found for '{query}'.")

        view = GoogleSearchView(results, query)
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
        
        msg = await interaction.followup.send(f"<:search:1338134220718997625> | Image searching for '{query}'. This may take a while. <:happy_tracker:1329914691656614042>")

        msgid = msg.id

        # Set search parameters
        search_params = {
            'q': query,
            'num': 10,  # Number of results to fetch
            'safe': 'high',  # Ensures that results are safe for work (SFW)
            'fileType': 'png',  # Only JPG and PNG images
        }

        gis.search(search_params=search_params)
        
        images = [result.url for result in gis.results()] if gis.results() else []

        if images:
            view = ImageSearchView(images, query, timeout=300)
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
            f"**Owner**: {server.owner.mention}\n"
            f"**Member Count**: {server.member_count}\n"
            f"**Created At**: <t:{creation_time}:f>"
        )
        embed.set_thumbnail(url=server.icon.url)
        embed.set_footer(text="ServerInfo | Tracker",
            icon_url="https://i.imgur.com/J8jXkhj.png")
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
                 icon_url="https://i.imgur.com/J8jXkhj.png")
        await interaction.response.send_message(embed=embed)

# SERVERICON
    @app_commands.command()
    async def servericon(self, interaction: discord.Interaction):
        """Send the server's icon."""
        server_icon = interaction.guild.icon.url 
        embed = discord.Embed(colour=0xad7e66)

        embed.set_image(url=f"{server_icon}")

        embed.set_footer(text="ServerIcon | Tracker",
                 icon_url="https://i.imgur.com/J8jXkhj.png")
        await interaction.response.send_message(embed=embed)

# USERINFO
    @app_commands.command()
    @app_commands.describe(member="The user you want info for.")
    async def userinfo(self, interaction: discord.Interaction, member: discord.Member = None):
        """Shows some generic user info."""
        if member is None:
            member = interaction.user

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
        now = datetime.now(timezone.utc)
        created_at = f"<t:{int(member.created_at.timestamp())}:f> (<t:{int(member.created_at.timestamp())}:R>)"
        joined_at = f"<t:{int(member.joined_at.timestamp())}:f> (<t:{int((now - member.joined_at).total_seconds())}:R>)"

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
            icon_url="https://i.imgur.com/J8jXkhj.png")

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
                 icon_url="https://i.imgur.com/J8jXkhj.png")

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
            await log_error(interaction.guild, bot, interaction.command.name, "Failed to generate petpet GIF. The API may be down.")
            return
        
        gif_url = response.json().get("url")
        if not gif_url:
            await log_error(interaction.guild, bot, interaction.command.name, "Failed to retrieve petpet GIF. API response was invalid.")
            return
        
        gif_response = requests.get(gif_url)
        if gif_response.status_code != 200:
            await log_error(interaction.guild, bot, interaction.command.name, "Failed to download the GIF.")
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
    async def furry(self, interaction: discord.Interaction):
        """Sends a random Furry gif."""
        api_instance = giphy_client.DefaultApi()
        api_key = 'gC9drTTPIu9gfjNEBk8xDIW6ff8CG8bd'
        tag = 'fursuit'
        try:
            while True:
                api_response = api_instance.gifs_random_get(api_key, tag=tag)
                blacklist = ["https://giphy.com/gifs/motion-capture-abillmiller-a-bill-miller-ch1cijjnCVK2T656w1"]
                if api_response.data.url not in blacklist:
                    await interaction.response.send_message(api_response.data.url)
                    break
        except ApiException as e:
            await log_error(interaction.guild, bot, interaction.command.name, f"Failed to retrieve GIF from Giphy API. Error: {e}")

fun_commands = Fun(name="fun", description="Fun Commands.")

async def setup(bot):
    bot.tree.add_command(fun_commands)