from bs4 import BeautifulSoup
from urllib.parse import urlencode
from aiohttp import ClientSession

from storygraph_bot.settings import SETTINGS

class FlareClient:

    def __init__(self):
        self.session = None

    async def setup(self):
        self.client = ClientSession(base_url=SETTINGS.flaresolverr_url)
        sess_req = await (await self.client.post("v1", json={"cmd": "sessions.create"})).json()
        self.session = sess_req["session"]
        print(sess_req)

    async def close(self):
        sess_req = await self.client.post("v1", json={"cmd": "sessions.destroy", "session": self.session})
        print(await sess_req.json())
        await self.client.close()

    async def _req(self, cmd: str, args: dict = {}) -> BeautifulSoup:
        req = await self.client.post("v1", json={
            "cmd": cmd,
            "session": self.session,
            **args
        })
        try:
            html = (await req.json())["solution"]["response"]
        except KeyError:
            print("Cannot parse flaresolverr response: ", req.json())
            raise KeyError
        return BeautifulSoup(html, "lxml")

    async def get(self, url) -> BeautifulSoup:
        return await self._req("request.get", {"url": url})

    async def post(self, url: str, data: dict[str, str], args: dict = {}) -> BeautifulSoup:
        return await self._req("request.post", {"url": url, "postData": urlencode(data), **args})
