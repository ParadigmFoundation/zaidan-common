from unittest import TestCase, main

from zaidan import is_valid_uuid, encode_to_bytes, decode_from_bytes

string_data = "abcdefghijklmnopqrstuv"
string_data_compressable = "aaaaaaaaaaaaaaaaaaaaaa"
structured_data_base_case = {'a': 1, 'b': '2',
                             'c': ['d', 1, {'e': 2}, []], 'f': {'g': 42}}
structured_data_compressable = {'a': 1, 'b': '2',
                                'c': ['d', 1, {'a': 1}, []], 'f': {'a': 1}}


class TestUtils(TestCase):

    def test_is_valid_uuid(self):
        from uuid import uuid4

        uuid_ish_string = "c8ea170bf4ce42d39de4f48b68d5106e"

        self.assertTrue(is_valid_uuid(str(uuid4()), 4),
                        "should validate uuid v4")
        self.assertFalse(is_valid_uuid(uuid_ish_string),
                         "should not validate bad uuid")

    def test_encode_to_bytes(self):
        structured_data_base_case_compressed = encode_to_bytes(
            structured_data_base_case)
        structured_data_compressable_compressed = encode_to_bytes(
            structured_data_compressable)
        string_data_compressed = encode_to_bytes(string_data)
        string_data_compressable_compressed = encode_to_bytes(
            string_data_compressable)

        self.assertGreater(
            len(string_data_compressed), len(string_data_compressable_compressed))
        self.assertGreater(len(structured_data_base_case_compressed), len(
            structured_data_compressable_compressed))

    def test_decode_from_bytes(self):
        compressed = encode_to_bytes(structured_data_compressable)
        recovered = decode_from_bytes(compressed)

        self.assertDictEqual(structured_data_compressable, recovered)


if __name__ == "__main__":
    main()
