import json
from typing import Any, Callable, Dict, Literal, Optional, Union
from app.configs.redis_config import get_redis_client
from app.core.logger import logger


class RedisHelper:
    @staticmethod
    def _make_key(base_key: str, unique_key: Optional[str] = None) -> str:
        return f"{base_key}-{unique_key}" if unique_key else base_key

    @staticmethod
    async def redis_set(
        key: str,
        value: Dict[str, Any],
        expiry: Optional[int] = None,
        data_actions: Optional[Dict[str, Any]] = None,
    ) -> bool:
        try:
            redis_client = await get_redis_client()
            if data_actions and data_actions.get("setAsArray"):
                unique_key = data_actions["uniqueKey"]
                redis_key = RedisHelper._make_key(key, value[unique_key])
                existing_data = await redis_client.get(redis_key)
                data_array = json.loads(existing_data) if existing_data else []

                action = data_actions.get("actionIfExists", "append")

                if action == "delete":
                    updated_array = [
                        entry for entry in data_array if entry.get(unique_key) != value[unique_key]
                    ]
                elif action == "replace":
                    updated_array = [
                        entry for entry in data_array if entry.get(unique_key) != value[unique_key]
                    ]
                    updated_array.append(value)
                else:
                    updated_array = data_array + [value]

                data_str = json.dumps(updated_array)
                if expiry:
                    await redis_client.setex(redis_key, expiry, data_str)
                else:
                    await redis_client.set(redis_key, data_str)
            else:
                if data_actions and "uniqueKey" in data_actions:
                    unique_key = value[data_actions["uniqueKey"]]
                    redis_key = RedisHelper._make_key(key, unique_key)
                    data_str = json.dumps(value)

                    if expiry:
                        await redis_client.setex(redis_key, expiry, data_str)
                    else:
                        await redis_client.set(redis_key, data_str)
                else:
                    logger.warning("uniqueKey is missing in dataActions.")
            return True
        except Exception as e:
            logger.error(f"Error in RedisHelper.redis_set: {e}")
            return False

    @staticmethod
    async def redis_get(key: str) -> Optional[Dict[str, Any]]:
        try:
            redis_client = await get_redis_client()
            result = await redis_client.get(key)
            if not result:
                logger.warning(f"Key not found in Redis: {key}")
                return None
            return json.loads(result)
        except Exception as e:
            logger.error(f"Error in RedisHelper.redis_get for key {key}: {e}")
            return None

    @staticmethod
    async def redis_delete(key: str) -> bool:
        try:
            redis_client = await get_redis_client()
            result = await redis_client.delete(key)

            print(result, 'redisResult')
            if result == 0:
                logger.warning(f"Key not found in Redis: {key}")
                return False
            logger.info(f"Key deleted successfully from Redis: {key}")
            return True
        except Exception as e:
            logger.error(f"Error in RedisHelper.redis_delete for key {key}: {e}")
            return False

