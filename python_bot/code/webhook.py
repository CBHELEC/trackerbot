from dotenv import load_dotenv
load_dotenv(verbose=True, override=True)

import topgg
import os

TOPGG_AUTH = os.getenv("TOPGG_AUTH")

# this can be async too!
@topgg.endpoint("/dblwebhook", topgg.WebhookType.BOT, TOPGG_AUTH)
def endpoint(
    vote_data: topgg.BotVoteData,
    # uncomment this if you want to get access to client
    # client: discord.Client = topgg.data(discord.Client),
):
    # this function will be called whenever someone votes for your bot.
    print("Received a vote!", vote_data)

    # do anything with client here
    # client.dispatch("dbl_vote", vote_data)
