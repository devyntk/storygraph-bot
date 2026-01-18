import re

from bs4 import Tag

from storygraph_bot.flare_client import FlareClient
from storygraph_bot.news_parser import NewsItem, parse_news_item
from storygraph_bot.util import assert_tag, canonicalize_url


def _get_authenticity_token(tag: Tag) -> str:
    authenticity_input = tag.find(attrs={"name": "authenticity_token"})
    if authenticity_input is None:
        raise ValueError("Could not find Authenticity Token")
    return str(authenticity_input.attrs.get("value"))


class StorygraphClient:

    async def setup(self):
        self.client = FlareClient()
        await self.client.setup()

    async def close(self):
        await self.client.close()

    async def log_in(self, username: str, password: str):
        login_page = await self.client.get(
            "https://app.thestorygraph.com/users/sign_in"
        )

        await self.client.post(
            "https://app.thestorygraph.com/users/sign_in",
            {
                "authenticity_token": _get_authenticity_token(login_page),
                "user[email]": username,
                "user[password]": password,
                "user[remember_me]": "1",
                "return_to": "",
            },
        )

    async def accept_all_friend_requests(self):
        notifications = await self.client.get(
            "https://app.thestorygraph.com/notifications"
        )
        accept_buttons = notifications.find_all(
            "form", action=re.compile(".*accept-friend-request-from-notification.*")
        )
        for button in accept_buttons:
            url = canonicalize_url(str(button.attrs.get("action")))
            token = _get_authenticity_token(button)
            print(url, token)
            print(self.client.post(url, {"authenticity_token": token}))

    async def get_community_activity(self) -> list[NewsItem]:
        community = await self.client.get("https://app.thestorygraph.com/community")
        news_feed = community.find(class_="news-feed-item-panes")
        assert assert_tag(news_feed)
        return [parse_news_item(child) for child in news_feed.find_all(recursive=False)]
