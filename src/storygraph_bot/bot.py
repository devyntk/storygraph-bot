import discord
from discord.ext import tasks

from storygraph_bot.flare_client import FlareError
from storygraph_bot.newness_cache import NewnessCache
from storygraph_bot.news_parser import render_news_item
from storygraph_bot.settings import SETTINGS
from storygraph_bot.storygraph_client import StorygraphClient


class StorygraphBot(discord.Client):
    # Suppress error on the User attribute being None since it fills up later
    user: discord.ClientUser  # pyright: ignore

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.storygraph = StorygraphClient()
        self.newness = NewnessCache()

    async def setup_hook(self) -> None:
        await self.storygraph.setup()
        await self.storygraph.log_in(SETTINGS.storygraph_email, SETTINGS.storygraph_password)
        # start the task to run in the background
        self.check_for_new_items.start()
        self.check_for_new_items.add_exception_type(FlareError)

    async def close(self):
        # do your cleanup here
        await self.storygraph.close()

        await super().close()  # don't forget this!

    async def on_ready(self):
        print(f'Logged in as {self.user} (ID: {self.user.id})')
        print('------')

    @tasks.loop(seconds=60)
    async def check_for_new_items(self):
        channel = self.get_channel(SETTINGS.discord_channel)
        # Tell the type checker that this is a messageable channel
        assert isinstance(channel, discord.abc.Messageable)

        news = await self.storygraph.get_community_activity()
        async for item in self.newness.filter_seen(news):
            await channel.send(embed=render_news_item(item))


    @check_for_new_items.before_loop
    async def before_my_task(self):
        await self.wait_until_ready()  # wait until the bot logs in
