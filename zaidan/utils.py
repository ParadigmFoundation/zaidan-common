from base64 import b64encode, b64decode
from gzip import compress, decompress
from json import dumps, loads
from uuid import uuid4, UUID


def is_valid_uuid(uuid_to_test: str, version=4) -> bool:
    """
    Check if uuid_to_test is a valid UUID.

    :param uuid_to_test: The UUID being validated.
    :param version: Optionally specify UUID version (default: 4).
    """
    try:
        uuid_obj = UUID(uuid_to_test, version=version)
    except ValueError:
        return False

    return str(uuid_obj) == uuid_to_test


def encode_to_bytes(data: object, str_encoding='utf-8') -> bytes:
    '''
    Encode and compress structured data to a base-64 encoded bytestring.

    :param data: The structured data to encode and compress.
    '''

    try:
        data_str = dumps(data)
        data_bytes = bytes(data_str, str_encoding)
        compressed = compress(data_bytes)
        encoded = b64encode(compressed)
        return encoded
    except Exception as error:
        raise Exception('failed to compress data: {}'.format(error.args))


def decode_from_bytes(data: bytes, str_encoding='utf-8') -> object:
    '''
    Decode and decompress structured data from a base-64 encoded bytestring.

    :param data: The encoded and compressed structured data as a bytestring.
    '''

    try:
        decoded = b64decode(data)
        decompressed = decompress(decoded)
        data_str = decompressed.decode(str_encoding)
        return loads(data_str)
    except Exception as error:
        raise Exception('failed to decompress data: {}'.format(error.args))
