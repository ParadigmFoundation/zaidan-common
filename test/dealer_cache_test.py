from unittest import TestCase, main
from uuid import uuid4
from time import time, sleep

from redis import Redis

from zaidan import DealerCache, encode_to_bytes, decode_from_bytes, OutOfDateError

''' Unhedged position test values. '''
# structure: [ [symbol, name], ]
test_vals = [['WETH/DAI', 123.5], ['ETH/USD', 0.88], ['ZRX/DAI', 471]]

''' Order book test values. '''
test_exchange_name = "coinbarf"
test_market_symbol = "SPANK/USD"
test_bid_order_book = [[1.5, 0.01], [1.4, 0.02], [1.3, 0.04], [1.1, 1.3]]
test_ask_order_book = [[1.6, 0.02], [1.7, 0.04], [2.1, 0.88], [2.4, 2.08]]


def make_test_quote(size: float, price: float, side: str) -> tuple:
    return (str(uuid4()), {'size': size, 'price': price, 'side': side, 'expiration': int(time()) + 35})


class TestDealerCache(TestCase):

    redis = Redis()

    # main test instance
    db = DealerCache()

    def _clear_test_books(self):
        for side in ('bid', 'ask'):
            self.redis.delete(
                f'{test_exchange_name}_{test_market_symbol}_{side}')

    def _clear_test_positions(self):
        ids = self.redis.hgetall(DealerCache.unhedged_position_key)
        return [self.redis.hdel(DealerCache.unhedged_position_key, _id) for _id in ids]

    def _clear_test_quotes(self):
        ids = self.redis.hgetall(DealerCache.order_marks_key)
        return [self.redis.hdel(DealerCache.order_marks_key, _id) for _id in ids]

    def test_set_unhedged_position(self):
        self._clear_test_positions()

        for test_val in test_vals:
            symbol = test_val[0]
            position = test_val[1]

            self.db.set_unhedged_position(symbol, position)
            from_redis = self.redis.hget(self.db.unhedged_position_key, symbol)
            self.assertEqual(from_redis.decode(), str(position))

    def test_get_unhedged_position(self):
        self._clear_test_positions()

        for test_val in test_vals:
            symbol = test_val[0]
            position = test_val[1]

            before = self.db.get_unhedged_position(symbol)
            self.assertEqual(before, 0.0)

            self.db.set_unhedged_position(symbol, position)
            after = self.db.get_unhedged_position(symbol)
            self.assertEqual(after, position)

    def test_set_order_book(self):
        self._clear_test_books()

        compressed_ask_book = encode_to_bytes(test_ask_order_book)
        compressed_bid_book = encode_to_bytes(test_bid_order_book)

        self.db.set_order_book(test_exchange_name,
                               test_market_symbol, 'ask', test_ask_order_book)
        self.db.set_order_book(test_exchange_name,
                               test_market_symbol, 'bid', test_bid_order_book)

        raw_asks_from_redis = self.redis.get(
            f'{test_market_symbol}_{test_exchange_name}_ask')
        raw_bids_from_redis = self.redis.get(
            f'{test_market_symbol}_{test_exchange_name}_bid')
        self.assertEqual(raw_asks_from_redis, compressed_ask_book)
        self.assertEqual(raw_bids_from_redis, compressed_bid_book)

    def test_get_order_book(self):
        self._clear_test_books()

        self.db.set_order_book(test_exchange_name,
                               test_market_symbol, 'ask', test_ask_order_book)
        self.db.set_order_book(test_exchange_name,
                               test_market_symbol, 'bid', test_bid_order_book)

        raw_asks_from_redis = self.redis.get(
            f'{test_market_symbol}_{test_exchange_name}_ask')
        raw_bids_from_redis = self.redis.get(
            f'{test_market_symbol}_{test_exchange_name}_bid')

        asks_from_redis = decode_from_bytes(raw_asks_from_redis)
        bids_from_redis = decode_from_bytes(raw_bids_from_redis)

        asks = self.db.get_order_book(
            test_exchange_name, test_market_symbol, 'ask')
        bids = self.db.get_order_book(
            test_exchange_name, test_market_symbol, 'bid')

        self.assertListEqual(asks, asks_from_redis)
        self.assertListEqual(bids, bids_from_redis)

    def test_get_expired_book(self):
        self._clear_test_books()

        self.db.set_order_book(test_exchange_name,
                               test_market_symbol, 'ask', test_ask_order_book)
        sleep(0.01)
        with self.assertRaises(OutOfDateError):
            self.db.get_order_book(
                test_exchange_name, test_market_symbol, 'ask', 0.01)

    def test_set_quote(self):
        self._clear_test_quotes()

        quotes = []
        quote_ids = []

        sides = ('bid', 'ask')
        for i in range(1, 11):
            mark = make_test_quote(i, 1/i, sides[i % 2])
            quote_ids.append(mark[0])
            quotes.append(mark)
            self.db.set_quote(mark[0], mark[1])

        quote_ids_from_redis = self.redis.hkeys(DealerCache.order_marks_key)
        quote_ids_from_method = self.db.get_quote_ids()

        quote_ids.sort()
        quote_ids_from_method.sort()

        self.assertTrue(len(quote_ids_from_redis), len(quote_ids_from_method))
        self.assertListEqual(quote_ids, quote_ids_from_method)

    def test_get_quote(self):
        self._clear_test_quotes()

        quotes = []
        quote_ids = []

        sides = ('bid', 'ask')
        for i in range(1, 11):
            mark = make_test_quote(i, 1/i, sides[i % 2])
            quote_ids.append(mark[0])
            quotes.append(mark)
            self.db.set_quote(mark[0], mark[1])
            quote_from_method = self.db.get_quote(mark[0])
            self.assertDictEqual(quote_from_method, mark[1])

    def test_update_quote_status(self):
        self._clear_test_quotes()

        order_mark = make_test_quote(1.1, 0.88, 'bid')
        quote_id = order_mark[0]
        quote = order_mark[1]

        self.db.set_quote(quote_id, quote)
        got_quote_status = self.db.get_quote_status(quote_id)
        self.assertEqual(got_quote_status, 0)

        self.db.update_quote_status(quote_id, 1)
        got_quote_status = self.db.get_quote_status(quote_id)
        self.assertEqual(got_quote_status, 1)

    def test_get_all_order_marks(self):
        self._clear_test_quotes()

        quotes = {}

        sides = ('bid', 'ask')
        for i in range(1, 11):
            mark = make_test_quote(i, 1/i, sides[i % 2])
            quotes[mark[0]] = mark[1]
            self.db.set_quote(mark[0], mark[1])

        got_quotes = self.db.get_all_order_marks(False)
        self.assertEqual(len(got_quotes.keys()), len(quotes.keys()))

        # if we set an expired quote, it shouldn't show up when True is the param
        expired_quote_id = str(uuid4())
        expired_quote = make_test_quote(1.33, 0.42, 'bid')[1]
        expired_quote['expiration'] = int(time()) - 1
        quotes[expired_quote_id] = expired_quote
        self.db.set_quote(expired_quote_id, expired_quote)

        # should include expired quote
        new_quotes = self.db.get_all_order_marks(False)
        self.assertIn(expired_quote_id, new_quotes)

        only_valid_quotes = self.db.get_all_order_marks(True)
        self.assertNotIn(expired_quote_id, only_valid_quotes)

    def test_remove_order_mark(self):
        self._clear_test_quotes()

        new_mark = make_test_quote(1.2, 2.1, 'bid')
        quote_id = new_mark[0]
        quote = new_mark[1]
        self.assertFalse(self.redis.hexists(
            DealerCache.order_marks_key, quote_id))
        self.db.set_quote(quote_id, quote)
        self.assertTrue(self.redis.hexists(
            DealerCache.order_marks_key, quote_id))
        self.db.remove_order_mark(quote_id)
        self.assertFalse(self.redis.hexists(
            DealerCache.order_marks_key, quote_id))

    def test_get_quote_ids(self):
        self._clear_test_quotes()

        expected_ids = []

        self.assertListEqual(expected_ids, self.db.get_quote_ids())
        self.assertEqual(len(self.db.get_quote_ids()), 0)

        mark = make_test_quote(1.22, 3.11, 'ask')
        quote_id = mark[0]
        quote = mark[1]

        self.db.set_quote(quote_id, quote)
        expected_ids.append(quote_id)

        quote_id_list = self.db.get_quote_ids()
        self.assertListEqual(quote_id_list, expected_ids)


if __name__ == "__main__":
    main()
