import json
import dataclasses
import logging
from typing import AsyncIterator

import aiofiles
import json_tricks

from storygraph_bot.news_parser import NewsItem
from storygraph_bot.settings import SETTINGS


class NewnessCache:
    """Determine if we've seen a piece of news before or not"""

    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.first_run = True
        self.seen: set = set()

    async def filter_seen(self, items: list[NewsItem]) -> AsyncIterator[NewsItem]:
        if not SETTINGS.seen_db.exists():
            async with aiofiles.open(SETTINGS.seen_db, "w") as f:
                self.logger.info("No DB exists, creating empty")
                await f.write("[]")

        async with aiofiles.open(SETTINGS.seen_db, "r+") as f:
            try:
                for seen_item in json_tricks.loads((await f.read()).strip()):
                    db_item = NewsItem(**seen_item)
                    self.seen.add(db_item)
            except json.JSONDecodeError:
                self.logger.exception("Unable to read JSON, proceeding as if DB was empty")


            if self.first_run:
                if len(self.seen) == 0:
                    self.logger.info("No items in DB, caching all currently seen IDs")
                    for item in items:
                        self.seen.add(item)

                self.first_run = False

            for item in items:
                if item not in self.seen:
                    yield item
                    self.seen.add(item)

            await f.seek(0)
            await f.write(json_tricks.dumps([dataclasses.asdict(o) for o in self.seen], indent=4))
            await f.truncate()
