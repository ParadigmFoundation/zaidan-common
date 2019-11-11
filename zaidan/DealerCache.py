from sys import path
from time import time

from redis import Redis

from .utils import is_valid_uuid, encode_to_bytes, decode_from_bytes


class DealerCacheError(Exception):
    ''' Signifies an error encountered while interacting with the cache. '''


class NotFoundError(DealerCacheError):
    ''' Signifies an error arising when a requested item does not exist. '''


class OutOfDateError(DealerCacheError):
    ''' Signifies a record is out-of-date according to specified parameters. '''


class DealerCache():
    '''
    Abstraction over a Redis database for dealer quotes and orders.

    Provides compression/encoding for storing structured data in redis.
    '''

    # redis key for quotes (order mark) hash table
    order_marks_key = "ORDER_MARKS"

    # redis key for per-symbol un-hedged positions hash table
    unhedged_position_key = "UNHEDGED_POSITION"

    def __init__(self, host: str, port=6379, password=None):
        '''
        Create a new DealerCache instance.

        :param host: The hostname of the Redis server.
        :param port: The port of the Redis server (default: 6379)
        :param password: The password for the Redis server (default: None)
        '''

        self.db = Redis(host=host, port=port, password=password)

    def set_unhedged_position(self, symbol: str, size: float) -> None:
        '''
        Set a new value for the per-symbol un-hedged position.

        :param symbol: The market symbol (BASE/QUOTE) format.
        :param size: The floating-point value of the un-hedged position.
        '''

        size_val = str(size)
        self.db.hset(self.unhedged_positions_key, symbol.upper(), size_val)

    def get_unhedged_position(self, symbol: str) -> float:
        '''
        Get the value for the per-symbol un-hedged position. If no value is
        present, float(0.0) will be returned.

        :param symbol: The market symbol (BASE/QUOTE) format.
        '''

        if not self.db.hexists(self.unhedged_position_key, symbol.upper()):
            return 0.0

        str_val = self.db.hget(self.unhedged_position_key, symbol)
        return float(str_val)

    def get_order_book(self, exchange: str, symbol: str, side: str, max_age=20) -> list:
        '''
        Fetch and decode an order book from the cache by exchage/size/side.

        If the book is out-of-date according to the max_age parameter, an
        OutOfDateError is raised. Set a max_age of 0 to skip the age check.

        :param exchange: The name of the exchange hosting the market.
        :param symbol: The currency pair (BASE/QUOTE) of the market to get.
        :param side: The side (bid or ask) of the book to get.
        :param max_age: The maximum age (in seconds) of the book data.
        '''

        # record call time to use for expiration check
        call_time = time()

        symbols = symbol.split('/')
        if len(symbols) != 2:
            raise ValueError('symbol must be BASE_TICKER/QUOTE_TICKER format')

        base_key = f'{symbol.upper()}_{exchange.lower()}_{side.lower()}'
        timestamp_key = f'{base_key}_timestamp'

        book_timestamp = self.db.get(timestamp_key)
        book_age = call_time - float(book_timestamp)
        if max_age > 0 and book_age >= max_age:
            raise OutOfDateError(f'book is {book_age - max_age}s out of date')

        raw_book = self.db.get(base_key)
        return decode_from_bytes(raw_book)

    def set_quote(self, quote_id: str, order_mark: object, status=0) -> None:
        '''
        Store an order mark object by its quote UUID.

        Used to initially store quotes, and to update their statuses.

        Status codes:
        - 0: Quote generated
        - 1: Validated and submitted for settlement
        - 2: Filled, sent to hedger

        :param quote_id: The quote UUID string.
        :param order_mark: The quote object.
        :param status: The new status of the quote.
        '''

        data = {'status': status, 'quote': order_mark}

        mark_compressed = encode_to_bytes(order_mark)
        self.db.hset(self.order_marks_key, quote_id, mark_compressed)

    def update_quote_status(self, quote_id: str, new_status: int) -> None:
        '''
        Update an existing quote's status.

        :param quote_id: The ID of the quote to update.
        :param new_status: The new status code of the quote.
        '''

        if not self.db.hexists(self.order_marks_key, quote_id):
            raise NotFoundError('quote with specified ID not found')

        order_mark_raw = self.db.hget(self.order_marks_key, quote_id)
        order_mark = decode_from_bytes(order_mark_raw)

        if 'status' not in order_mark:
            raise DealerCacheError('malformed order mark; no known status')

        order_mark['status'] = new_status
        new_mark_raw = encode_to_bytes(order_mark)
        self.db.hset(self.order_marks_key, quote_id, new_mark_raw)

    def get_quote(self, quote_id: str) -> object:
        '''
        Fetch an order mark by it's quote ID (if it exists).

        Will raise a NotFoundError if the quote does not exist, and a CacheError
        if the quote_id is invalid.

        :param quote_id: The quote ID generated on initial request.
        '''

        if not is_valid_uuid(quote_id):
            raise DealerCacheError("invalid quote ID")

        raw_order_mark = self.db.hget(self.order_marks_key, quote_id)
        if not raw_order_mark:
            raise NotFoundError("quote not found", quote_id)

        order_mark = decode_from_bytes(raw_order_mark)
        return order_mark['quote']

    def get_all_order_marks(self, only_valid=True) -> dict:
        '''
        Fetch a dictionary with all order marks (price quotes and statuses).

        :param only_valid: If set, (default) only non-expired result included.
        '''

        call_time = time()

        marks = {}
        raw_marks = self.db.hgetall(self.order_marks_key)
        for mark_id in raw_marks.keys():
            decoded_mark = decode_from_bytes(raw_marks[mark_id])

            if only_valid and int(time) >= int(decoded_mark['quote']['expiration']):
                continue

            quotes[mark_id] = decoded_mark

        return quotes

    def remove_order_mark(self, quote_id: str) -> None:
        '''
        Remove an order mark by its ID.

        :param quote_id: The UUID included when the quote was generated.
        '''

        self.db.hdel(self.order_marks_key, quote_id)

    def get_quote_ids(self) -> list:
        '''
        Fetch an array of all quote ID's in the cache.
        '''

        return self.db.hkeys(self.order_marks_key)
