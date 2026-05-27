from __future__ import annotations

import asyncio
from typing import Any

import aiobotocore.session

from voice_server.config import get_settings
from voice_server.observability.logging import get_logger

logger = get_logger(__name__)

_client_session: aiobotocore.session.AioSession | None = None


def _get_session() -> aiobotocore.session.AioSession:
    global _client_session
    if _client_session is None:
        _client_session = aiobotocore.session.get_session()
    return _client_session


def _client_kwargs() -> dict[str, Any]:
    settings = get_settings()
    kwargs: dict[str, Any] = {"region_name": "us-east-1"}
    if settings.dynamo_endpoint_url:
        kwargs["endpoint_url"] = settings.dynamo_endpoint_url
    return kwargs


async def get_dynamo_client():
    session = _get_session()
    return session.create_client("dynamodb", **_client_kwargs())


async def put_item(item: dict[str, Any]) -> bool:
    settings = get_settings()
    try:
        async with await get_dynamo_client() as client:
            await client.put_item(TableName=settings.dynamo_table_name, Item=item)
        return True
    except Exception as e:
        logger.warning("dynamo_put_failed", error=str(e))
        return False


async def get_item(key: dict[str, Any], consistent: bool = True) -> dict[str, Any] | None:
    settings = get_settings()
    try:
        async with await get_dynamo_client() as client:
            response = await client.get_item(
                TableName=settings.dynamo_table_name,
                Key=key,
                ConsistentRead=consistent,
            )
        return response.get("Item")
    except Exception as e:
        logger.warning("dynamo_get_failed", error=str(e))
        return None


async def query_by_pk(session_id: str, consistent: bool = True) -> list[dict[str, Any]]:
    settings = get_settings()
    try:
        async with await get_dynamo_client() as client:
            response = await client.query(
                TableName=settings.dynamo_table_name,
                KeyConditionExpression="session_id = :sid",
                ExpressionAttributeValues={":sid": {"S": session_id}},
                ConsistentRead=consistent,
            )
        return response.get("Items", [])
    except Exception as e:
        logger.warning("dynamo_query_failed", error=str(e))
        return []


async def query_gsi(index_name: str, pk_value: str) -> list[dict[str, Any]]:
    settings = get_settings()
    try:
        async with await get_dynamo_client() as client:
            response = await client.query(
                TableName=settings.dynamo_table_name,
                IndexName=index_name,
                KeyConditionExpression="#s = :val",
                ExpressionAttributeNames={"#s": "status"},
                ExpressionAttributeValues={":val": {"S": pk_value}},
            )
        return response.get("Items", [])
    except Exception as e:
        logger.warning("dynamo_gsi_query_failed", error=str(e))
        return []


async def delete_item(key: dict[str, Any]) -> bool:
    settings = get_settings()
    try:
        async with await get_dynamo_client() as client:
            await client.delete_item(TableName=settings.dynamo_table_name, Key=key)
        return True
    except Exception as e:
        logger.warning("dynamo_delete_failed", error=str(e))
        return False


def batch_write_sync(items: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Synchronous batch write for shutdown drain. Returns unprocessed items."""
    import boto3

    settings = get_settings()
    kwargs: dict[str, Any] = {"region_name": "us-east-1"}
    if settings.dynamo_endpoint_url:
        kwargs["endpoint_url"] = settings.dynamo_endpoint_url

    client = boto3.client("dynamodb", **kwargs)
    unprocessed: list[dict[str, Any]] = []

    for i in range(0, len(items), 25):
        batch = items[i : i + 25]
        request_items = {
            settings.dynamo_table_name: [{"PutRequest": {"Item": item}} for item in batch]
        }
        try:
            response = client.batch_write_item(RequestItems=request_items)
            failed = response.get("UnprocessedItems", {}).get(settings.dynamo_table_name, [])
            unprocessed.extend(failed)
        except Exception as e:
            logger.error("batch_write_failed", error=str(e), batch_size=len(batch))
            unprocessed.extend(batch)

    return unprocessed
