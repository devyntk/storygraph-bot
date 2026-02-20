import logging
from argparse import ArgumentParser

from storygraph_bot.discord.commands import bot
from storygraph_bot.settings import SETTINGS


def main():
    parser = ArgumentParser()
    parser.add_argument("-d", "--debug", action="store_true")
    args = parser.parse_args()
    logging.basicConfig(level=logging.DEBUG if args.debug else logging.INFO)
    bot.run(SETTINGS.discord_token)
