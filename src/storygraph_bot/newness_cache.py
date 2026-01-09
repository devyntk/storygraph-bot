import json
import dataclasses

import aiofiles

from storygraph_bot.news_parser import NewsItem
from storygraph_bot.settings import settings


class NewnessCache:
    """Determine if we've seen a piece of news before or not"""

    def __init__(self):
        self.first_run = True
        self.seen: set = set()

    async def filter_seen(self, items: list[NewsItem]) -> list[NewsItem]:
        if not settings.seen_db.exists():
            async with aiofiles.open(settings.seen_db, "w") as f:
                await f.write("[]")

        new_items = []
        async with aiofiles.open(settings.seen_db, "r+") as f:
            try:
                for seen_item in json.loads((await f.read()).strip()):
                    db_item = NewsItem(**seen_item)
                    self.seen.add(db_item)
            except json.JSONDecodeError as e:
                print(e)
                print("Unable to read JSON, proceeding as if DB was empty")


            if self.first_run:
                if len(self.seen) == 0:
                    print("No items in DB, caching all currently seen IDs")
                    for item in items:
                        self.seen.add(item)

                self.first_run = False

            for item in items:
                if item not in self.seen:
                    new_items.append(item)
                    self.seen.add(item)

            await f.seek(0)
            await f.write(json.dumps([dataclasses.asdict(o) for o in self.seen]))
            await f.truncate()

        return new_items
