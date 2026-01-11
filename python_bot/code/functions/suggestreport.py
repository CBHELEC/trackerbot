import discord
import os

class FullModal(discord.ui.Modal, title="Suggest or Report"):
    def __init__(self, bot, interaction: discord.Interaction):
        super().__init__()
        self.interaction = interaction
        self.bot = bot
    select_label = discord.ui.Label(
        text="Pick an option",
        component=discord.ui.Select(
            placeholder="Bug Report or Feature Suggestion",
            min_values=1,
            max_values=1,
            options=[
                discord.SelectOption(label="Suggest a Feature"),
                discord.SelectOption(label="Report a Bug"),
            ],
            required=True
        ),
        description="Select an option to proceed"
    )

    text_input_label = discord.ui.Label(
        text="Your Report/Suggestion",
        component=discord.ui.TextInput(
            style=discord.TextStyle.short,
            placeholder="Type something here...",
            required=True
        ),
        description="This is your suggestion or bug report content"
    )

    async def on_submit(self, modal_interaction: discord.Interaction):
        select_value = self.select_label.component.values[0]
        text_value = self.text_input_label.component.value
        msg = "suggestion" if select_value == "Suggest a Feature" else "bug report"
        msg2 = "Suggestion" if select_value == "Suggest a Feature" else "Bug Report"
        await modal_interaction.response.send_message(
            f"Thank you for your {msg}! The Dev will review it ASAP.", ephemeral=True
        )
        embed = discord.Embed(title=f"New {msg}!",
                description=f"User: {self.interaction.user.mention}\nType: {msg2}\nContent: {text_value}",
                colour=0xad7e66)
        await self.bot.get_channel(int(os.getenv('SUGGEST_REPORT_CHANNEL_ID'))).send(f"<@{os.getenv('DEV_USER_ID')}> New Suggestion/Bug Report!", embed=embed)