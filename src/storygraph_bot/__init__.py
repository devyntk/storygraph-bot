import logging

from storygraph_bot.discord.commands import bot
from storygraph_bot.settings import SETTINGS

logging.basicConfig(level=logging.INFO)

def main():
    bot.run(SETTINGS.discord_token)
