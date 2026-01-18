import logging

import discord
from storygraph_bot.discord.client import StorygraphBot

bot = StorygraphBot(intents=discord.Intents.default())

logger = logging.getLogger(__name__)

@bot.event
async def on_ready():
    assert bot.user is not None
    logger.info(f'Logged in as {bot.user} (ID: {bot.user.id})')


@bot.slash_command()
async def follow(ctx: discord.ApplicationContext):
    await ctx.respond("Hello!")

