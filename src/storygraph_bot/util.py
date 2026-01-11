from urllib.parse import urlparse

def canonicalize_url(url_in: str) -> str:
    url = urlparse(url_in, scheme="https")
    if not url.netloc:
        url = url._replace(netloc="app.thestorygraph.com")
    return url.geturl()
