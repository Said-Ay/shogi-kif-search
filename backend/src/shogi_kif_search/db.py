# Copyright (C) 2026 Said-Ay
# SPDX-License-Identifier: GPL-3.0-only

"""PostgreSQLに保存するためのテーブルと型を定義する。"""

from typing import TYPE_CHECKING, override

from sqlalchemy import BigInteger
from sqlalchemy.types import TypeDecorator

if TYPE_CHECKING:
    from sqlalchemy.engine import Dialect

# 64ビットの最上位のビット=2^63
UINT64_SIGN_BIT = 1 << 63

# 64ビットで表せる値の個数=2^64
UINT64_RANGE = 1 << 64


def to_signed(value: int) -> int:
    """64ビットの符号なし整数をビットの並びを変えずに符号付き整数として読み替える。

    Args:
        value: 符号なし整数。

    Returns:
        符号付き整数。

    Raises:
        ValueError: 64ビットの符号なし整数の範囲外の場合。
    """
    if not 0 <= value < UINT64_RANGE:
        msg = "値が範囲外です。0以上 2^64-1 以下の整数を指定してください。"
        raise ValueError(msg)
    if value >= UINT64_SIGN_BIT:
        return value - UINT64_RANGE
    return value


def to_unsigned(value: int) -> int:
    """64ビットの符号付き整数をビットの並びを変えずに符号なし整数として読み替える。`to_signed` の逆。

    Args:
        value: 符号付き整数。

    Returns:
        符号なし整数。

    Raises:
        ValueError: 64ビットの符号付き整数の範囲外の場合。
    """
    if not -UINT64_SIGN_BIT <= value < UINT64_SIGN_BIT:
        msg = "値が範囲外です。-2^63以上 2^63-1 以下の整数を指定してください。"
        raise ValueError(msg)
    if value < 0:
        return value + UINT64_RANGE
    return value


class PositionHash(TypeDecorator[int]):
    """局面ハッシュの列の型。Pythonでは符号なし、PostgreSQLでは符号付きの `bigint` として扱う。"""

    impl = BigInteger
    cache_ok = True

    @override
    def process_bind_param(self, value: int | None, dialect: Dialect) -> int | None:
        """保存するときに符号なしから符号付きに変換する。"""
        if value is None:
            return None
        return to_signed(value)

    @override
    def process_result_value(self, value: object | None, dialect: Dialect) -> int | None:
        """読み出すときに符号付きから符号なしに変換する。"""
        if value is None:
            return None
        if not isinstance(value, int):
            msg = "値の型が不正です。intである必要があります。"
            raise TypeError(msg)
        return to_unsigned(value)
