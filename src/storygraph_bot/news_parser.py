from datetime import datetime
import re
from dataclasses import dataclass, field

from bs4 import Tag
from discord import Embed
import dateparser

from storygraph_bot.util import canonicalize_url

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
    rating: float | None

    action: str

    timestamp: datetime | None = field(hash=False, compare=False, default=None)


def parse_news_item(tag: Tag) -> NewsItem:
    id = str(tag.attrs.get("data-news-feed-item-id"))

    first_string = [str(o) for o in tag.strings if str(o).strip()][0]
    timestamp =  dateparser.parse(first_string, languages=["en"])

    profile_link_tag = tag.find("a", href=re.compile("profile"))
    assert profile_link_tag is not None
    profile_link = str(profile_link_tag.attrs.get("href"))

    profile_div = profile_link_tag.parent
    assert profile_div is not None

    action = str(
        profile_div.find(string=lambda f: f is not None and f not in profile_link)
    ).strip()
    username = str(
        profile_div.find(string=lambda f: f is not None and f in profile_link)
    ).strip()

    profile_div = profile_div.parent
    assert profile_div is not None
    profile_img = profile_div.find("img")
    profile_img_url = (
        str(profile_img.attrs.get("src")) if profile_img is not None else None
    )

    book_cover_div = tag.find("div", class_="book-cover")
    assert book_cover_div is not None
    book_cover_url_img = book_cover_div.find("img")
    assert book_cover_url_img is not None
    book_cover_url = str(book_cover_url_img["src"])

    book_title_section = tag.find("div", class_="book-title-and-author")
    assert book_title_section is not None

    book_link_tag = book_title_section.find("a", href=re.compile("books"))
    assert book_link_tag is not None
    book_link = str(book_link_tag.attrs.get("href"))
    book_name = str(book_link_tag.string)

    author_link_tag = book_title_section.find("a", href=re.compile("authors"))
    assert author_link_tag is not None
    author_link = str(author_link_tag.attrs.get("href"))
    author_name = str(author_link_tag.string)

    review_link_tag = tag.find("a", href=re.compile("reviews"))
    if review_link_tag is not None:
        review_link = canonicalize_url(str(review_link_tag.attrs.get("href")))
    else:
        review_link = None

    star_tag = tag.find("svg", class_="icon-star")
    if star_tag is not None:
        rating_div = star_tag.find_previous_sibling(
            "span",
        )
        assert rating_div is not None
        rating = float(str(rating_div.string))
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
        rating=rating,
    )


def render_news_item(item: NewsItem) -> Embed:
    print(item)
    embed = Embed(
        title=item.book_name,
        url=item.review_link or item.book_link,
        timestamp=item.timestamp,
    )
    embed.set_thumbnail(url=item.book_cover_url)
    embed.set_author(
        name=f"{item.username} {item.action}",
        url=item.profile_link,
        icon_url=item.profile_image_url,
    )

    description = f"""by [{item.author_name}]({item.author_link})"""
    if item.rating:
        description += f"""\n{item.rating} {"⭐" * int(item.rating)}"""

    embed.description = description
    return embed
