from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_ignore_empty=True)

    API_ID: int
    API_HASH: str

    AUTO_UPGRADE_STORAGE: bool = False
    AUTO_UPGRADE_MINING: bool = False
    AUTO_UPGRADE_HOLY: bool = False
    AUTO_CLEAR_TASKS: bool = False
    AUTO_START_HUNT: bool = False

    AUTO_SELL_WORMS: bool = True
    QUANTITY_TO_KEEP: dict = {
        "common": {
            "quantity_to_keep": 2,
            "sale_price": 1
        },
        "uncommon": {
            "quantity_to_keep": 2,
            "sale_price": 0
        },
        "rare": {
            "quantity_to_keep": -1,
            "sale_price": 0
        },
        "epic": {
            "quantity_to_keep": -1,
            "sale_price": 0
        },
        "legendary": {
            "quantity_to_keep": -1,
            "sale_price": 0
        }
    }

    USE_PROXY_FROM_FILE: bool = False

settings = Settings()


