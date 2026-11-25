# Copyright (C) 2026 Said-Ay
# SPDX-License-Identifier: GPL-3.0-only

"""db.pyのテスト。"""

from typing import TYPE_CHECKING

import pytest

from shogi_kif_search.db import to_signed, to_unsigned

if TYPE_CHECKING:
    from collections.abc import Callable


@pytest.mark.parametrize(
    ("unsigned", "signed"),
    [(0, 0), (2**63 - 1, 2**63 - 1), (2**63, -(2**63)), (2**64 - 1, -1)],
)
def test_boundary(unsigned: int, signed: int) -> None:
    """境界の値で、符号なしと符号付きが互いに読み替えられることを確認する。"""
    assert to_signed(unsigned) == signed
    assert to_unsigned(signed) == unsigned


@pytest.mark.parametrize(
    ("convert", "value"),
    [
        pytest.param(to_signed, -1, id="to_signed_negative"),
        pytest.param(to_signed, 2**64, id="to_signed_too_large"),
        pytest.param(to_unsigned, -(2**63) - 1, id="to_unsigned_too_small"),
        pytest.param(to_unsigned, 2**63, id="to_unsigned_too_large"),
    ],
)
def test_out_of_range(convert: Callable[[int], int], value: int) -> None:
    """64ビットの範囲外の値はValueErrorになることを確認する。"""
    with pytest.raises(ValueError, match="値が範囲外です。"):
        convert(value)
