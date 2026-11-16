# Copyright (C) 2026 Said-Ay
# SPDX-License-Identifier: GPL-3.0-only

"""move.pyのテスト。"""

import pytest

from shogi_kif_search.move import DropMove, NormalMove, Square
from shogi_kif_search.piece import PieceKind


@pytest.mark.parametrize(
    ("file", "rank", "message"),
    [(0, 5, "筋は1から9の整数です。"), (5, 10, "段は1から9の整数です。")],
)
def test_square_out_of_range(file: int, rank: int, message: str) -> None:
    """筋か段が1から9の範囲外のマス目はValueErrorになることを確認する。"""
    with pytest.raises(ValueError, match=message):
        Square(file, rank)


def test_normal_move_same_square() -> None:
    """移動元と移動先が同じ手はValueErrorになることを確認する。"""
    with pytest.raises(ValueError, match="同じマス目に移動できません。"):
        NormalMove(Square(7, 7), Square(7, 7), promote=False)


def test_drop_king() -> None:
    """玉を打つ手はValueErrorになることを確認する。"""
    with pytest.raises(ValueError, match="玉は打てません。"):
        DropMove(Square(5, 5), PieceKind.KING)


def test_move_is_hashable() -> None:
    """同じ内容の指し手は等しく、辞書のキーに使えることを確認する。"""
    moves = {NormalMove(Square(7, 7), Square(7, 6), promote=False): "7g7f"}
    assert moves[NormalMove(Square(7, 7), Square(7, 6), promote=False)] == "7g7f"
