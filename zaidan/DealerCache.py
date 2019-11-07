from sys import path

from redis import Redis

from .utils import is_valid_uuid, encode_to_bytes, decode_from_bytes


class DealerCacheError(Exception):
    ''' Signifies an error encountered while interacting with the cache. '''


class NotFoundError(DealerCacheError):
    ''' Signifies an error arising when a requested item does not exist. '''


class DealerCache():
    '''
    Abstraction over a Redis database for dealer quotes and orders.

    Provides compression/encoding for storing structured data in redis.
    '''

    # redis key for quotes (order mark) hash table
    quotes_key = "QUOTES"

    # redis key for orders hash table (hedger positions)
    orders_key = "ORDERS"

    def __init__(self, host: str, port=6379, password=None):
        '''
        Create a new DealerCache instance.

        :param host: The hostname of the Redis server.
        :param port: The port of the Redis server (default: 6379)
        :param password: The password for the Redis server (default: None)
        '''

        self.db = Redis(host=host, port=port, password=password)

    def set_quote(self, quote_id: str, order_mark: object) -> None:
        '''
        Store an order mark object by its quote UUID.

        Used to initially store quotes, and to update their statuses.

        :param quote_id: The quote UUID string.
        :param order_mark: The quote object.
        '''

        mark_compressed = encode_to_bytes(order_mark)
        self.db.hset(self.quotes_key, quote_id, mark_compressed)

    def get_quote(self, quote_id: str) -> object:
        '''
        Fetch an order mark by it's quote ID (if it exists).

        Will raise a NotFoundError if the quote does not exist, and a CacheError
        if the quote_id is invalid.

        :param quote_id: The quote ID generated on initial request.
        '''

        if not is_valid_uuid(quote_id):
            raise DealerCacheError("invalid quote ID")

        raw_order_mark = self.db.hget(self.quotes_key, quote_id)
        if not raw_order_mark:
            raise NotFoundError("quote not found", quote_id)

        order_mark = decode_from_bytes(raw_order_mark)
        return order_mark
