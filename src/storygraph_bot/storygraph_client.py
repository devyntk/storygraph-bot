from enum import Enum, auto
import logging
import re

from bs4 import Tag

from storygraph_bot.flare_client import FlareClient
from storygraph_bot.news_parser import NewsItem, parse_news_item
from storygraph_bot.util import TagFindError, assert_tag, canonicalize_url


def _get_authenticity_token(tag: Tag) -> str:
    authenticity_input = tag.find(attrs={"name": "authenticity_token"})
    if authenticity_input is None:
        raise TagFindError("Could not find Authenticity Token")
    return str(authenticity_input.attrs.get("value"))


class FollowResult(Enum):
    Followed = auto()
    FriendRequestSent = auto()
    NoOptions = auto()
    NoProfile = auto()
    Error = auto()



class StorygraphClient:

    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.client = FlareClient()

    async def setup(self):
        await self.client.setup()

    async def close(self):
        if self.client:
            await self.client.close()

    async def log_in(self, username: str, password: str):
        self.logger.info("Logging into storygraph user %s", username)
        login_page = await self.client.get(
            "https://app.thestorygraph.com/users/sign_in"
        )

        await self.client.post(
            "https://app.thestorygraph.com/users/sign_in",
            {
                "authenticity_token": _get_authenticity_token(login_page.body),
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
        accept_buttons = notifications.body.find_all(
            "form", action=re.compile(".*accept-friend-request-from-notification.*")
        )
        for button in accept_buttons:
            url = canonicalize_url(str(button.attrs.get("action")))
            token = _get_authenticity_token(button)
            await self.client.post(url, {"authenticity_token": token})

    async def get_community_activity(self) -> list[NewsItem]:
        self.logger.info("Fetching community activity")
        community = await self.client.get("https://app.thestorygraph.com/community")
        news_feed = community.body.find(class_="news-feed-item-panes")
        assert assert_tag(news_feed)
        return [parse_news_item(child) for child in news_feed.find_all(recursive=False)]

    async def attempt_follow(self, username: str) -> tuple[FollowResult, str | None]:
        profile = await self.client.get(f"https://app.thestorygraph.com/profile/{username}")
        username_check = profile.body.find(text=re.compile(username))
        if username_check is None:
            return (FollowResult.NoProfile, None)

        follow_form = profile.body.find("form", action=re.compile(r"follows\.js"))
        if follow_form:
            follow_value_name ="followed_user_id"
            user_id_input = follow_form.find(attrs={"name": follow_value_name})
            if user_id_input is None:
                return (FollowResult.Error, None)
            user_id = str(user_id_input["value"])

            auth_token = _get_authenticity_token(follow_form)
            url = canonicalize_url(str(follow_form.attrs.get("action")))
            print(url)

            res = await self.client.post(url, {"authenticity_token": auth_token, follow_value_name: user_id}, )
            print(res.status)
            return (FollowResult.Followed, user_id)


        friend_form = profile.body.find("form", action=re.compile(r"friend_requests\.js"))
        if friend_form:
            friend_value_name ="pending_friend_id"
            user_id_input = friend_form.find(attrs={"name": friend_value_name})
            if user_id_input is None:
                return (FollowResult.Error, None)
            user_id = str(user_id_input["value"])

            auth_token = _get_authenticity_token(friend_form)
            url = canonicalize_url(str(friend_form.attrs.get("action")))

            res = await self.client.post(url, {"authenticity_token": auth_token, friend_value_name: user_id})
            print(res.status, res.body)
            return (FollowResult.FriendRequestSent, user_id)


        return (FollowResult.NoOptions, None)

