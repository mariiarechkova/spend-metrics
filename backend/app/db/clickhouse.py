import asyncio

import clickhouse_connect

from app.core.config import settings

_client = None


def get_clickhouse_client():
    global _client
    if _client is None:
        _client = clickhouse_connect.get_client(
            host=settings.clickhouse_host,
            port=settings.clickhouse_port,
            database=settings.clickhouse_db,
            username=settings.clickhouse_user,
            password=settings.clickhouse_password,
        )
    return _client


def _init_clickhouse_sync() -> None:
    bootstrap_client = clickhouse_connect.get_client(
        host=settings.clickhouse_host,
        port=settings.clickhouse_port,
        username=settings.clickhouse_user,
        password=settings.clickhouse_password,
    )
    bootstrap_client.command(f"CREATE DATABASE IF NOT EXISTS {settings.clickhouse_db}")

    client = get_clickhouse_client()
    client.command(
        """
        CREATE TABLE IF NOT EXISTS leads (
            id UUID,
            user_id UUID,
            source_type String,
            source_id Nullable(UUID),
            utm_source String,
            utm_medium String,
            utm_campaign String,
            utm_content String,
            campaign_id String,
            name String,
            contact String,
            raw_data String,
            created_at DateTime DEFAULT now()
        ) ENGINE = MergeTree()
        ORDER BY (user_id, created_at)
        """
    )

    client.command(
        """
        CREATE TABLE IF NOT EXISTS ad_spend (
            id UUID,
            user_id UUID,
            provider String,
            campaign_id String,
            campaign_name String,
            spend Decimal(10, 2),
            impressions UInt64,
            clicks UInt64,
            date Date,
            synced_at DateTime DEFAULT now()
        ) ENGINE = MergeTree()
        ORDER BY (user_id, provider, date)
        """
    )

    client.command(
        """
        CREATE TABLE IF NOT EXISTS app_metrics (
            timestamp DateTime DEFAULT now(),
            metric_name String,
            value Float64,
            labels String
        ) ENGINE = MergeTree()
        ORDER BY (timestamp, metric_name)
        """
    )


async def init_clickhouse() -> None:
    await asyncio.to_thread(_init_clickhouse_sync)
