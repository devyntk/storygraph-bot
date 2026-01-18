from typing import TypeGuard
from urllib.parse import urlparse


class TagFindError(Exception):
    pass


def assert_tag[T](tag: T | None) -> TypeGuard[T]:
    if tag is None:
        raise TagFindError
    return True


def canonicalize_url(url_in: str) -> str:
    url = urlparse(url_in, scheme="https")
    if not url.netloc:
        url = url._replace(netloc="app.thestorygraph.com")
    return url.geturl()
