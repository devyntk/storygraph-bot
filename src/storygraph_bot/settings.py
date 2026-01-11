from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import EmailStr

class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file='.env', env_file_encoding='utf-8')

    storygraph_email: EmailStr
    storygraph_password: str

    discord_token: str
    discord_channel: int

    seen_db: Path = Path("news.db")

    flaresolverr_url: str = "http://localhost:8191/"

SETTINGS = Settings()  # pyright: ignore
