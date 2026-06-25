from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict
from functools import lru_cache


class Settings(BaseSettings):

    APP_NAME: str = "Reservoir Water Quality Monitor"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False

    # 数据库配置
    MYSQL_HOST: str = "localhost"
    MYSQL_PORT: int = 3306
    MYSQL_USER: str = "root"
    MYSQL_PASSWORD: str = ""
    MYSQL_DATABASE: str = "water_quality_monitor"

    # Redis 配置
    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379

    # Neo4j 配置
    NEO4J_URI: str = "bolt://localhost:7687"
    NEO4J_USER: str = "neo4j"
    NEO4J_PASSWORD: str = "admin123"

    # Chroma 配置
    CHROMA_PERSIST_DIR: str = "chroma_data"
    COLLECTION_NAME: str = "water_knowledge"

    # JWT 配置
    JWT_SECRET_KEY: str = "change-me"
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRE_MINUTES: int = 1440

    # CORS 配置
    CORS_ORIGINS: list[str] = ["http://localhost:3444"]

    # 对话推理模型配置
    CHAT_API_KEY: str = ""
    CHAT_BASE_URL: str = "https://api.deepseek.cn/v1"
    CHAT_MODEL: str = "deepseek-v4-flash"

    # 嵌入模型配置
    EMBEDDING_API_KEY: str = ""
    EMBEDDING_BASE_URL: str = "https://dashscope.aliyuncs.com/compatible-mode/v1"
    EMBEDDING_MODEL: str = "text-embedding-v4"

    @property
    def DATABASE_URL(self) -> str:
        return (
            f"mysql+pymysql://{self.MYSQL_USER}:{self.MYSQL_PASSWORD}"
            f"@{self.MYSQL_HOST}:{self.MYSQL_PORT}/{self.MYSQL_DATABASE}"
            f"?charset=utf8mb4"
        )

    @property
    def ASYNC_DATABASE_URL(self) -> str:
        return (
            f"mysql+aiomysql://{self.MYSQL_USER}:{self.MYSQL_PASSWORD}"
            f"@{self.MYSQL_HOST}:{self.MYSQL_PORT}/{self.MYSQL_DATABASE}"
            f"?charset=utf8mb4"
        )

    UPDATE_PATH_NAME: str = "update"

    CHUNK_SIZE: int = 2000
    CHUNK_OVERLAP: int = 240
    SEPARATORS: list[str] = ["\n\n", "\n", "。", "！", "？", ".", "!", "?", " ", ""]

    TOP_K: int = 5

    PATROL_ANALYSIS_INTERVAL: int = 43200  # 秒，默认 12 小时

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


@lru_cache()
def get_settings():
    return Settings()


settings = get_settings()
