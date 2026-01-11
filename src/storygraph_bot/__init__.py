import discord

from storygraph_bot.settings import SETTINGS
from storygraph_bot.bot import StorygraphBot


def main():
    client = StorygraphBot(intents=discord.Intents.default())
    client.run(SETTINGS.discord_token)
