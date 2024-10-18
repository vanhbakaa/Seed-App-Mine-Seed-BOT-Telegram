from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_ignore_empty=True)

    API_ID: int
    API_HASH: str

    REF_LINK: str = "t.me/seed_coin_bot/app?startapp=6493211155"

    AUTO_UPGRADE_STORAGE: bool = True
    AUTO_UPGRADE_MINING: bool = True
    AUTO_UPGRADE_HOLY: bool = True
    AUTO_CLEAR_TASKS: bool = True
    AUTO_START_HUNT: bool = True

    AUTO_SPIN: bool = True
    SPIN_PER_ROUND: list[int] = [5, 10]
    AUTO_FUSION: bool = True
    MAXIMUM_PRICE_TO_FUSION_COMMON: int = 30
    MAXIMUM_PRICE_TO_FUSION_UNCOMMON: int = 200
    MAXIMUM_PRICE_TO_FUSION_RARE: int = 800
    MAXIMUM_PRICE_TO_FUSION_EPIC: int = 3000
    MAXIMUM_PRICE_TO_FUSION_LEGENDARY: int = 20000

    AUTO_SELL_WORMS: bool = False
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


