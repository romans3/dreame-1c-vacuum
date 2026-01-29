"""miIO protocol implementation

This module contains the implementation of the routines to encrypt and decrypt
miIO payloads with a device-specific token.
"""

import calendar
import datetime
import hashlib
import json
import logging
from typing import Any, Dict, Tuple

from construct import (
    Adapter,
    Bytes,
    Checksum,
    Const,
    Default,
    GreedyBytes,
    Hex,
    IfThenElse,
    Int16ub,
    Int32ub,
    Pointer,
    RawCopy,
    Rebuild,
    Struct,
)
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import padding
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes

_LOGGER = logging.getLogger(__name__)


# --- Wrapper per compatibilità ---
def utc_from_timestamp(ts: int) -> datetime.datetime:
    """Restituisce un datetime UTC timezone-aware (compatibile con Python <3.12)."""
    try:
        return datetime.datetime.fromtimestamp(ts, datetime.UTC)
    except AttributeError:
        # Fallback per versioni più vecchie
        return datetime.datetime.utcfromtimestamp(ts)


class Utils:
    """Utility functions for miIO protocol."""

    @staticmethod
    def verify_token(token: bytes):
        if not isinstance(token, bytes):
            raise TypeError("Token must be bytes")
        if len(token) != 16:
            raise ValueError("Wrong token length")

    @staticmethod
    def md5(data: bytes) -> bytes:
        checksum = hashlib.md5()
        checksum.update(data)
        return checksum.digest()

    @staticmethod
    def key_iv(token: bytes) -> Tuple[bytes, bytes]:
        key = Utils.md5(token)
        iv = Utils.md5(key + token)
        return key, iv

    @staticmethod
    def encrypt(plaintext: bytes, token: bytes) -> bytes:
        if not isinstance(plaintext, bytes):
            raise TypeError("plaintext requires bytes")
        Utils.verify_token(token)
        key, iv = Utils.key_iv(token)
        padder = padding.PKCS7(128).padder()
        padded_plaintext = padder.update(plaintext) + padder.finalize()
        cipher = Cipher(algorithms.AES(key), modes.CBC(iv), backend=default_backend())
        encryptor = cipher.encryptor()
        return encryptor.update(padded_plaintext) + encryptor.finalize()

    @staticmethod
    def decrypt(ciphertext: bytes, token: bytes) -> bytes:
        if not isinstance(ciphertext, bytes):
            raise TypeError("ciphertext requires bytes")
        Utils.verify_token(token)
        key, iv = Utils.key_iv(token)
        cipher = Cipher(algorithms.AES(key), modes.CBC(iv), backend=default_backend())
        decryptor = cipher.decryptor()
        padded_plaintext = decryptor.update(ciphertext) + decryptor.finalize()
        unpadder = padding.PKCS7(128).unpadder()
        unpadded_plaintext = unpadder.update(padded_plaintext)
        unpadded_plaintext += unpadder.finalize()
        return unpadded_plaintext

    @staticmethod
    def checksum_field_bytes(ctx: Dict[str, Any]) -> bytearray:
        x = bytearray(ctx["header"].data)
        x += ctx["_"]["token"]
        if "data" in ctx:
            x += ctx["data"].data
        return x

    @staticmethod
    def get_length(x) -> int:
        datalen = x._.data.length
        return datalen + 32

    @staticmethod
    def is_hello(x) -> bool:
        if "length" in x:
            val = x["length"]
        else:
            val = x.header.value["length"]
        return bool(val == 32)


class TimeAdapter(Adapter):
    """Adapter per conversione timestamp."""

    def _encode(self, obj, context, path):
        return int(obj.timestamp())

    def _decode(self, obj, context, path):
        # Usa wrapper retrocompatibile
        return utc_from_timestamp(obj)


class EncryptionAdapter(Adapter):
    def _encode(self, obj, context, path):
        return Utils.encrypt(
            json.dumps(obj).encode("utf-8") + b"\x00", context["_"]["token"]
        )

    def _decode(self, obj, context, path):
        try:
            decrypted = Utils.decrypt(obj, context["_"]["token"])
            decrypted = decrypted.rstrip(b"\x00")
        except Exception:
            _LOGGER.debug("Unable to decrypt, returning raw bytes: %s", obj)
            return obj

        decrypted_quirks = [
            lambda d: d,
            lambda d: d.replace(b',,"otu_stat"', b',"otu_stat"'),
            lambda d: d[: d.rfind(b"\x00")] if b"\x00" in d else d,
        ]

        for i, quirk in enumerate(decrypted_quirks):
            decoded = quirk(decrypted).decode("utf-8")
            try:
                return json.loads(decoded)
            except Exception as ex:
                if i == len(decrypted_quirks) - 1:
                    _LOGGER.error("unable to parse json '%s': %s", decoded, ex)

        return None


Message = Struct(
    "data" / Pointer(32, RawCopy(EncryptionAdapter(GreedyBytes))),
    "header"
    / RawCopy(
        Struct(
            Const(0x2131, Int16ub),
            "length" / Rebuild(Int16ub, Utils.get_length),
            "unknown" / Default(Int32ub, 0x00000000),
            "device_id" / Hex(Bytes(4)),
            "ts" / TimeAdapter(Default(Int32ub, datetime.datetime.now(datetime.UTC))),
        )
    ),
    "checksum"
    / IfThenElse(
        Utils.is_hello,
        Bytes(16),
        Checksum(Bytes(16), Utils.md5, Utils.checksum_field_bytes),
    ),
)
