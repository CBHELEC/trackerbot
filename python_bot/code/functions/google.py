import discord
from google_images_search import GoogleImagesSearch
from functions import static_var

class ImageSearchView(discord.ui.View):
    """View with buttons to navigate image search results."""
    def __init__(self, images, query, timeout: float = 50.0):
        super().__init__(timeout=timeout)
        self.images = images
        self.index = 0
        self.query = query
        self.msg = None
        self.update_buttons()

    async def on_timeout(self):
        """Disable all buttons when the view times out."""
        for button in self.children:
            button.disabled = True  
        if self.msg:
            await self.msg.edit(view=self)

    def update_buttons(self):
        """Update the state of navigation buttons."""
        for button in self.children:
            if button.custom_id == "first":
                button.disabled = self.index == 0
            elif button.custom_id == "previous":
                button.disabled = self.index == 0
            elif button.custom_id == "next":
                button.disabled = self.index >= len(self.images) - 1
            elif button.custom_id == "last":
                button.disabled = self.index >= len(self.images) - 1

    async def update_message(self, interaction: discord.Interaction):
        """Updates the embed with the new image result."""
        embed = discord.Embed(colour=0xad7e66)
        embed.set_footer(text=f"Image {self.index + 1} / 15 | {self.query} | Tracker",
        icon_url="https://i.imgur.com/kNe7FRh.png")
        embed.set_image(url=self.images[self.index])
        self.update_buttons()
        await interaction.response.edit_message(embed=embed, view=self)

    @discord.ui.button(emoji="<:first:1338154194640699442>", style=discord.ButtonStyle.primary, custom_id="first", disabled=True)
    async def first(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Go to the first image."""
        self.index = 0
        await self.update_message(interaction)

    @discord.ui.button(emoji="<:previous:1338154278589825114>", style=discord.ButtonStyle.primary, custom_id="previous", disabled=True)
    async def previous(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Go to the previous image."""
        if self.index > 0:
            self.index -= 1
        await self.update_message(interaction)

    @discord.ui.button(emoji="<:next:1338154251121332246>", style=discord.ButtonStyle.primary, custom_id="next")
    async def next(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Go to the next image."""
        if self.index < len(self.images) - 1:
            self.index += 1
        await self.update_message(interaction)

    @discord.ui.button(emoji="<:last:1338154217923416105>", style=discord.ButtonStyle.primary, custom_id="last")
    async def last(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Go to the last image."""
        self.index = len(self.images) - 1
        await self.update_message(interaction)
        
    @discord.ui.button(label="🔢", style=discord.ButtonStyle.primary)
    async def jump(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Go to a specified image."""
        
        class JumpModal(discord.ui.Modal, title="Jump to Page"):
            page_input = discord.ui.TextInput(
                label="Enter a page number 1-15",
                style=discord.TextStyle.short,
                required=True,
                min_length=1,
                max_length=2,
                placeholder="1-15"
            )

            async def on_submit(modal_self, modal_interaction: discord.Interaction):
                """Handles the submission of the page number."""
                try:
                    page = int(modal_self.page_input.value)
                    if 1 <= page <= 15:
                        self.index = page - 1
                        await self.update_message(modal_interaction)
                    else:
                        await modal_interaction.response.send_message("Invalid page number! Enter 1-15.", ephemeral=True)
                except ValueError:
                    await modal_interaction.response.send_message("Please enter a valid number.", ephemeral=True)

        await interaction.response.send_modal(JumpModal())

gis = GoogleImagesSearch(static_var.GOOGLE_API_KEY, static_var.GOOGLE_CX_ID)

def google_search(query):
    service = build("customsearch", "v1", developerKey=static_var.GOOGLE_NORMAL_API_KEY)
    res = service.cse().list(q=query, cx=static_var.GOOGLE_NORMAL_SEARCH_ID).execute()
    return res.get('items', [])

class GoogleSearchView(discord.ui.View):
    def __init__(self, results, query):
        super().__init__(timeout=300)
        self.results = results
        self.query = query
        self.index = 0
        self.update_buttons()

    def update_buttons(self):
        """Update button states based on current index."""
        self.first.disabled = self.index == 0
        self.previous.disabled = self.index == 0
        self.next.disabled = self.index == len(self.results) - 1
        self.last.disabled = self.index == len(self.results) - 1

    async def update_message(self, interaction: discord.Interaction):
        """Update the embed message and buttons."""
        result = self.results[self.index]
        embed = discord.Embed(
            title=result['title'],
            url=result['link'],
            description=result.get('snippet', ''),
            color=0xad7e66,
        )
        embed.set_footer(text=f"Result {self.index + 1} / {len(self.results)} | {self.query} | Tracker", 
                         icon_url="https://i.imgur.com/kNe7FRh.png")
        self.update_buttons()
        await interaction.response.edit_message(embed=embed, view=self)

    @discord.ui.button(emoji="<:first:1338154194640699442>", style=discord.ButtonStyle.primary, disabled=True)
    async def first(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Go to first result."""
        self.index = 0
        await self.update_message(interaction)

    @discord.ui.button(emoji="<:previous:1338154278589825114>", style=discord.ButtonStyle.primary, disabled=True)
    async def previous(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Go to previous result."""
        self.index = max(0, self.index - 1)
        await self.update_message(interaction)

    @discord.ui.button(emoji="<:next:1338154251121332246>", style=discord.ButtonStyle.primary)
    async def next(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Go to next result."""
        self.index = min(len(self.results) - 1, self.index + 1)
        await self.update_message(interaction)

    @discord.ui.button(emoji="<:last:1338154217923416105>", style=discord.ButtonStyle.primary)
    async def last(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Go to last result."""
        self.index = len(self.results) - 1
        await self.update_message(interaction)

    @discord.ui.button(label="🔢", style=discord.ButtonStyle.primary)
    async def jump(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Jump to a specified result."""
        class JumpModal(discord.ui.Modal, title="Jump to Page"):
            page_input = discord.ui.TextInput(
                label="Enter a page number",
                style=discord.TextStyle.short,
                required=True,
                min_length=1,
                max_length=2,
                placeholder=f"1-{len(self.results)}"
            )

            async def on_submit(modal_self, modal_interaction: discord.Interaction):
                try:
                    page = int(modal_self.page_input.value)
                    if 1 <= page <= len(self.results):
                        self.index = page - 1
                        await self.update_message(modal_interaction)
                    else:
                        await modal_interaction.response.send_message("Invalid page number!", ephemeral=True)
                except ValueError:
                    await modal_interaction.response.send_message("Please enter a valid number.", ephemeral=True)

        await interaction.response.send_modal(JumpModal())