import discord

class BadgeInfoView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=300)

        self.badge_embed = discord.Embed(title="What do the badges mean?",
                      description="Badges in the BadgeGen system have eight quality levels, from Bronze to Diamond, representing the user’s achievements. After reaching Diamond, users can unlock \"loops\" (additional levels) and \"Addons\" (extra mini-badges). Addons are often challenging, rewarding experienced Geocachers with special achievements, such as completing a calendar or attending specific events. Some badges also have specific loops and addon requirements, making them harder to achieve. \n\n**Full details on each badge can be found [here](https://project-gc.com/w/BadgeGen).**",
                      colour=0xad7e66)
        self.belt_embed = discord.Embed(title="What do the belts mean?",
                      description="**The Belt system is based on points, which are awarded based on various criteria. The sum of all points determines the user's overall belt level. There are 36 possible belts.**\n\nIf the user has fewer than 30 points, they will receive the White belt.\nAt 30 points, a Yellow belt will be awarded.\nEvery ten/twelve points after that will give the user an extra stripe on their belt.\nAfter 220 points, 12 points are required per level\nAfter 4 stripes, the user will be awarded a new colour belt.\nWith the exception of the black belt.\nAt 400 points, the Golden Black Belt (the highest ranking) is awarded.\n\n**Points are awarded based on the following conditions**:\n1 point per 100 caches found.\n2 points per event hosted, maximum of 30 points.\n0.5 points per difficulty/terrain combination found in excess of 40 combinations.\n10 points for completing the Difficulty/Terrain matrix.\n20 points for either finding caches in 15 distinct states or 5 distinct countries. 40 points are not awarded if both conditions are satisfied.\n10 points per 50 caches found on day with most finds, maximum of 40 points.\n0.5 points per 7 consecutive days with finds in largest streak. 10 point bonus at 366 days.\n0.1 points per favorite point on owned caches.\n2 points per distinct cache type on day with most distinct types found.\n2 points per distinct cache type hidden.\n2 points per distinct cache size hidden.\n0.5 points per FTF, maximum of 30 points.\n1 point per 5/5 Difficulty/Terrain cache found, maximum 5 points.\n1 point per gemstone badge (excluding country badges). [1]\n2 points for every year since the user's first cache find.\n0.08 points per calendar day cached on. No points awarded if distinct days is less than 100. The year is irrelevant.\n0.05 points per Trackable moved/discovered (maximum 25 points).\n0.1 points per photo uploaded to found logs (maximum 25 points).\n\n**For more info, [click here](<https://project-gc.com/w/BadgeGen_Belts>).**",
                      colour=0xad7e66)

    @discord.ui.button(label="Badge", style=discord.ButtonStyle.primary)
    async def badge_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Handles the Badge button click."""
        await interaction.response.edit_message(embed=self.badge_embed, view=BadgeInfoView())

    @discord.ui.button(label="Belt", style=discord.ButtonStyle.success)
    async def belt_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Handles the Belt button click."""
        await interaction.response.edit_message(embed=self.belt_embed, view=BadgeInfoView())