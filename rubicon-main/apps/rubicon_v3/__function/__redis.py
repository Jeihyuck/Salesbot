import json
import warnings

import redis

from alpha.settings import REDIS_ORCHESTRATOR_IP, REDIS_PORT, REDIS_PASSWORD

redis_client = redis.StrictRedis(
    host=REDIS_ORCHESTRATOR_IP,
    port=REDIS_PORT,
    db=0,
    password=REDIS_PASSWORD,
    ssl=True,
    decode_responses=True,
)


class RedisClient:
    CLIENT = redis.StrictRedis(
        host=REDIS_ORCHESTRATOR_IP,
        port=REDIS_PORT,
        db=0,
        password=REDIS_PASSWORD,
        ssl=True,
        decode_responses=True,
    )

    def __init__(self, client=CLIENT):
        super().__init__()
        self.client = client

    def store_dict(self, key, value: dict, expiry_seconds):
        """
        Redis에 사전을 저장합니다.

        Args:
            key (str): Redis 키.
            value (dict): 저장할 사전.
            expiry_seconds (int): 만료 시간(초).

        Returns:
            bool: 성공 여부.
        """
        try:
            # Convert any dictionary or list values to JSON strings
            o = {}
            for k, v in value.items():
                if isinstance(v, (list, tuple, set, dict)):
                    o[k] = json.dumps(v)
                else:
                    o[k] = str(v)

            with self.client.pipeline() as pipe:
                # No need to check existence since we want to create if doesn't exist
                pipe.multi()
                pipe.hset(key, mapping=o)
                pipe.expire(key, expiry_seconds)
                pipe.execute()

            return True

        except redis.RedisError as e:
            raise ValueError(f"Error storing data in Redis for key '{key}': {str(e)}")

    def get(self, key, fields=None):
        """
        Redis에서 사전 또는 특정 필드를 검색합니다.

        Args:
            key (str): Redis 키.
            fields (list, optional): 검색할 필드 목록.

        Returns:
            dict: 검색된 결과.
        """
        """
        Retrieve dictionary or specific fields from Redis, handling JSON-encoded values,
        boolean values, and raw strings.
        Returns False if key doesn't exist.
        """
        # @module_logger(message_id_param='message_id', module_name="get_stored_dict")

        try:
            if fields is None:
                result = self.client.hgetall(key)
                if not result:  # If empty dictionary returned
                    return {}
            else:
                if isinstance(fields, str):
                    fields = [fields]
                values = self.client.hmget(key, fields)
                # if all(v is None for v in values):
                #     return {fields: False} if isinstance(fields, str) else {f: False for f in fields}
                result = dict(zip(fields, values))
                result = {k: v for k, v in result.items() if v is not None}

            ret = {}
            for k, v in result.items():
                v = v.decode() if isinstance(v, bytes) else v

                if v == "True":
                    ret[k] = True
                elif v == "False":
                    ret[k] = False
                else:
                    try:
                        ret[k] = json.loads(v)
                    except (json.JSONDecodeError, TypeError):
                        ret[k] = v
            return ret

        except redis.RedisError as e:
            raise ValueError(f"Error accessing Redis for key '{key}': {str(e)}")

    def update(self, key, field, value):
        """
        Redis 해시의 필드를 새 값으로 업데이트합니다.

        Args:
            key (str): Redis 키.
            field (str): 업데이트할 필드.
            value (Any): 새 값.

        Returns:
            bool: 성공 여부.
        """
        """
        Update a field in a Redis hash with a new value.
        Only updates if the key already exists.
        Raises ValueError if key doesn't exist.
        The value will be JSON serialized before storage.
        """
        try:
            # Serialize the value
            if isinstance(value, (dict, list, tuple, set)):
                serialized_value = json.dumps(value)
            else:
                serialized_value = str(value)

            with self.client.pipeline() as pipe:
                while True:
                    try:
                        # Watch the key for changes
                        pipe.watch(key)

                        # Check if key exists
                        exists = self.CLIENT.exists(key)
                        if not exists:
                            pipe.unwatch()
                            raise ValueError(f"Key '{key}' doesn't exist")

                        # Start transaction
                        pipe.multi()
                        pipe.hset(key, field, serialized_value)
                        pipe.execute()
                        break

                    except redis.WatchError:
                        continue

            return True

        except redis.RedisError as e:
            raise ValueError(
                f"Error updating Redis for key '{key}', field '{field}': {str(e)}"
            )

    def exists(self, key):
        """
        Redis 키의 존재 여부를 확인합니다.

        Args:
            key (str): Redis 키.

        Returns:
            bool: 키가 존재하면 True, 그렇지 않으면 False.
        """
        return self.client.exists(key) == 1

    def append_to_dict_list(self, key, field, new_item):
        """
        해시 필드에 저장된 배열에 항목을 추가합니다.

        Args:
            key (str): Redis 키.
            field (str): 필드 이름.
            new_item (Any): 추가할 항목.

        Returns:
            bool: 성공 여부.
        """
        """
        Append an item to an array stored within a hash field.
        Only works with existing keys.
        Handles race conditions using Redis transactions.
        """

        try:
            with self.client.pipeline() as pipe:
                while True:
                    try:
                        # Watch the key for changes
                        pipe.watch(key)

                        # Check if key exists
                        exists = self.client.exists(key)
                        if not exists:
                            pipe.unwatch()
                            raise ValueError(f"Key '{key}' doesn't exist")

                        # Get current value
                        current_value = self.CLIENT.hget(key, field)

                        # Process the array
                        if current_value is None:
                            array = [new_item]
                        else:
                            current_value = (
                                current_value.decode()
                                if isinstance(current_value, bytes)
                                else current_value
                            )
                            array = json.loads(current_value)
                            if not isinstance(array, list):
                                array = [array]
                            array.append(new_item)

                        # Start transaction and update
                        pipe.multi()
                        pipe.hset(key, field, json.dumps(array))
                        pipe.execute()
                        break

                    except redis.WatchError:
                        continue
            return True

        except redis.RedisError as e:
            raise ValueError(
                f"Error updating Redis for key '{key}', field '{field}': {str(e)}"
            )
        except json.JSONDecodeError as e:
            raise ValueError(
                f"Error decoding JSON for key '{key}', field '{field}': {str(e)}"
            )

    def combine_dict_field(self, key, field_name, new_dict):
        """
        Redis 해시 필드에 저장된 사전에 새 사전을 병합합니다.

        Args:
            key (str): Redis 키.
            field_name (str): 필드 이름.
            new_dict (dict): 병합할 새 사전.

        Returns:
            None
        """
        current_dict = self.client.hget(key, field_name)
        if current_dict:
            try:
                current_dict = json.loads(current_dict)
            except json.JSONDecodeError:
                current_dict = {}
        else:
            current_dict = {}

        def recursive_update(dict1, dict2):
            for k, v in dict2.items():
                if k in dict1 and isinstance(dict1[k], dict) and isinstance(v, dict):
                    recursive_update(dict1[k], v)
                else:
                    dict1[k] = v
            return dict1

        merged_dict = recursive_update(current_dict, new_dict)

        self.client.hset(key, field_name, json.dumps(merged_dict))

# Deprecated
def store_dict_with_expiry(redis_client, key, dictionary, expiry_seconds, message_id):
    """
    Deprecated: Use RedisClient.store_dict() instead.

    Store a dictionary in Redis with expiration time.
    Creates the key if it doesn't exist, updates if it does.
    """
    warnings.warn("Deprecated. Use RedisClient.store_dict() instead.", DeprecationWarning, stacklevel=2)

    try:
        # Convert any dictionary or list values to JSON strings
        o = {}
        for k, v in dictionary.items():
            if isinstance(v, (list, tuple, set, dict)):
                o[k] = json.dumps(v)
            else:
                o[k] = str(v)

        with redis_client.pipeline() as pipe:
            # No need to check existence since we want to create if doesn't exist
            pipe.multi()
            pipe.hset(key, mapping=o)
            pipe.expire(key, expiry_seconds)
            pipe.execute()

        return True

    except redis.RedisError as e:
        raise ValueError(f"Error storing data in Redis for key '{key}': {str(e)}")