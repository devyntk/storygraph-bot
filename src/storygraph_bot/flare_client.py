import logging
from dataclasses import dataclass
from http import HTTPStatus
from urllib.parse import urlencode

from aiohttp import ClientError, ClientSession
from bs4 import BeautifulSoup

from storygraph_bot.settings import SETTINGS


class FlareError(Exception):
    pass

@dataclass()
class FlareResponse:
    body: BeautifulSoup
    status: HTTPStatus

class FlareClient:

    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.session = None
        self.client = None

    async def setup(self):
        self.client = ClientSession(base_url=SETTINGS.flaresolverr_url)
        sess_req = await (await self.client.post("v1", json={"cmd": "sessions.create"})).json()
        self.session = sess_req["session"]
        self.logger.info("established flaresolverr session %s", self.session)

    async def close(self):
        if self.client is not None:
            await self.client.post("v1", json={"cmd": "sessions.destroy", "session": self.session})
            self.logger.info("destroyed flaresolverr session %s", self.session)
            await self.client.close()

    async def _req(self, cmd: str, args: dict = {}) -> FlareResponse:
        assert self.client is not None
        try:
            req = await self.client.post("v1", json={
                "cmd": cmd,
                "session": self.session,
                **args
            })
        except ClientError as e:
            raise FlareError from e
        try:
            res = await req.json()
            html = res["solution"]["response"]
        except KeyError as e:
            self.logger.exception("Cannot parse flaresolverr response")
            raise FlareError from e
        return FlareResponse(
            body = BeautifulSoup(html, "lxml"),
            status = HTTPStatus(res["solution"]["status"])
        )

    async def get(self, url) -> FlareResponse:
        return await self._req("request.get", {"url": url})

    async def post(self, url: str, data: dict[str, str], args: dict = {}) -> FlareResponse:
        return await self._req("request.post", {"url": url, "postData": urlencode(data), **args})
