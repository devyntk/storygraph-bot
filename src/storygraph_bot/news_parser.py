from logging import getLogger
import re
from dataclasses import dataclass, field
from datetime import datetime
from decimal import Decimal

import dateparser
from bs4 import Tag
from discord import Embed

from storygraph_bot.util import assert_tag, canonicalize_url

logger = getLogger(__name__)

timestamp_re = re.compile(r"~(\d+[dmsw])")

@dataclass(unsafe_hash=True)
class NewsItem:
    id: str = field(hash=False, compare=False)

    username: str
    profile_link: str
    profile_image_url: str | None

    book_cover_url: str
    book_link: str
    book_name: str

    author_name: str
    author_link: str

    review_link: str | None
    rating: Decimal | None

    action: str

    review_content: str | None = None
    timestamp: datetime | None = field(hash=False, compare=False, default=None)


def parse_news_item(tag: Tag) -> NewsItem:
    id = str(tag.attrs.get("data-news-feed-item-id"))

    first_string = tag.find(string=timestamp_re)
    if first_string:
        assert first_string.string
        timestamp_str = f"{first_string.string} ago "
        timestamp =  dateparser.parse(timestamp_str, languages=["en"])
        logger.debug("timestamp: %s from %s", timestamp, timestamp_str)
    else:
        timestamp = None

    profile_link_tag = tag.find("a", href=re.compile("profile"))
    assert assert_tag(profile_link_tag)
    profile_link = str(profile_link_tag.attrs.get("href"))

    profile_div = profile_link_tag.parent
    assert assert_tag(profile_div)

    logger.debug("profile div strings: %s", list(profile_div.strings))
    action_div = profile_div.find(string=lambda f: f is not None and f.strip() != "" and f not in profile_link)
    action = str(action_div).strip()
    username = str(
        profile_div.find(string=lambda f: f is not None and f in profile_link)
    ).strip()

    profile_div = profile_div.parent
    assert assert_tag(profile_div)
    profile_img = profile_div.find("img")
    profile_img_url = (
        str(profile_img.attrs.get("src")) if profile_img is not None else None
    )

    book_cover_div = tag.find("div", class_="book-cover")
    assert assert_tag(book_cover_div)
    book_cover_url_img = book_cover_div.find("img")
    assert assert_tag(book_cover_url_img)
    book_cover_url = str(book_cover_url_img["src"])

    book_link_tags = tag.find_all("a", href=re.compile("books"))
    book_link_tags = list(filter(lambda t: t.find_parent("h4"), book_link_tags))
    book_link_tag =  book_link_tags[0] if len(book_link_tags) else None
    assert assert_tag(book_link_tag)
    book_link = str(book_link_tag.attrs.get("href"))
    book_name = str(book_link_tag.string)

    author_link_tags = tag.find_all("a", href=re.compile("authors"))
    author_link_tag = author_link_tags[0] if len(author_link_tags) else None
    assert assert_tag(author_link_tag)
    author_link = str(author_link_tag.attrs.get("href"))
    author_name = str(author_link_tag.string)

    review_link_tag = tag.find("a", href=re.compile("reviews"))
    if review_link_tag is not None:
        review_link_relative  = str(review_link_tag.attrs.get("href"))
        review_link = canonicalize_url(review_link_relative)

        review_content_tags = tag.find("a", href=review_link_relative, string=lambda f: f is not None and f not in action)
        if review_content_tags is not None:
            review_content = review_content_tags.string
        else:
            review_content = None
    else:
        review_link = None
        review_content = None

    rating_label = tag.find(attrs={"aria-label": re.compile("Rating: ")})
    if rating_label is not None:
        rating_str = list(filter(lambda t: t.strip(), rating_label.strings))
        logger.debug("rating label strings: %s", rating_str)
        rating = Decimal(str(rating_str[0])) if rating_str else None
    else:
        rating = None

    return NewsItem(
        id=id,
        timestamp=timestamp,
        profile_link=canonicalize_url(profile_link),
        profile_image_url=profile_img_url,
        username=username,
        action=action,
        book_cover_url=book_cover_url,
        book_name=book_name,
        book_link=canonicalize_url(book_link),
        author_name=author_name,
        author_link=canonicalize_url(author_link),
        review_link=review_link,
        review_content=review_content,
        rating=rating,
    )


def render_news_item(item: NewsItem) -> Embed:
    print(item)
    embed = Embed(
        title=item.book_name,
        url=item.review_link or item.book_link,
    )
    embed.set_thumbnail(url=item.book_cover_url)
    embed.set_author(
        name=f"{item.username} {item.action}",
        url=item.profile_link,
        icon_url=item.profile_image_url,
    )

    description = f"""by [{item.author_name}]({item.author_link})"""
    if item.rating:
        description += f"""\n{item.rating} {"⭐" * round(item.rating)}"""
    if item.review_content:
        description += f"\n{item.review_content}\n"
    if item.timestamp:
        description += f"\n<t:{int(item.timestamp.timestamp())}:R>"

    embed.description = description
    return embed
