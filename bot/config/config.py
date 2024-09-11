from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_ignore_empty=True)

    API_ID: int
    API_HASH: str

    AUTO_UPGRADE_STORAGE: bool = True
    AUTO_UPGRADE_MINING: bool = True
    AUTO_UPGRADE_HOLY: bool = True
    AUTO_CLEAR_TASKS: bool = True
    AUTO_START_HUNT: bool = True
    
    AUTO_SELL_WORMS: bool = True
    WORM_LVL_TO_SELL: int = 1
    PRICE_TO_SELL: int = 0

    USE_PROXY_FROM_FILE: bool = False


settings = Settings()

