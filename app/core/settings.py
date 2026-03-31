import os
from dataclasses import dataclass


@dataclass(frozen=True)
class Settings:
    database_url: str = os.getenv("RULE_API_DATABASE_URL", "sqlite:///./rule_api.db")
    create_tables: bool = os.getenv("RULE_API_CREATE_TABLES", "true").lower() in (
        "1",
        "true",
        "yes",
    )
    echo_sql: bool = os.getenv("RULE_API_SQL_ECHO", "false").lower() in (
        "1",
        "true",
        "yes",
    )


settings = Settings()
