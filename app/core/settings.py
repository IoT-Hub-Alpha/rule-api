import os
from dataclasses import dataclass


def _build_database_url() -> str:
    explicit = os.getenv("RULE_API_DATABASE_URL") or os.getenv("DATABASE_URL")
    if explicit:
        return explicit

    db_host = os.getenv("DB_HOST")
    if not db_host:
        raise ValueError(
            "Database configuration is missing. "
            "Set RULE_API_DATABASE_URL (preferred), DATABASE_URL, "
            "or DB_HOST/DB_PORT/DB_NAME/DB_USER/DB_PASSWORD."
        )

    db_user = os.getenv("DB_USER", "postgres")
    db_password = os.getenv("DB_PASSWORD", "postgres")
    db_name = os.getenv("DB_NAME", "postgres")
    db_port = os.getenv("DB_PORT", "5432")
    return (
        "postgresql+psycopg2://"
        f"{db_user}:{db_password}@{db_host}:{db_port}/{db_name}"
    )


@dataclass(frozen=True)
class Settings:
    database_url: str = _build_database_url()
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
