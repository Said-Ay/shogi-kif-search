# Copyright (C) 2026 Said-Ay
# SPDX-License-Identifier: GPL-3.0-only

"""move.pyのテスト。"""

import pytest

from shogi_kif_search.move import DropMove, NormalMove, Square
from shogi_kif_search.piece import HAND_PIECE_KINDS, PieceKind


@pytest.mark.parametrize(
    ("file", "rank"),
    [(1, 1), (9, 9)],
)
def test_square_valid(file: int, rank: int) -> None:
    """筋と段が1〜9ならSquareを生成できる。"""
    square = Square(file, rank)

    assert square.file == file
    assert square.rank == rank


@pytest.mark.parametrize(
    ("file", "rank"),
    [(0, 1), (10, 1), (1, 0), (1, 10)],
)
def test_square_invalid(file: int, rank: int) -> None:
    """筋または段が1〜9の範囲外ならValueErrorになる。"""
    with pytest.raises(ValueError, match="1から9までの整数"):
        Square(file, rank)


def test_normal_move_validity() -> None:
    """normal_moveを確認する。"""
    # 正しい指し手
    NormalMove(Square(1, 1), Square(2, 2), promote=False)
    NormalMove(Square(1, 1), Square(2, 2), promote=True)

    # 同じマス目に移動する指し手
    with pytest.raises(ValueError, match="同じマス目に移動できません。"):
        NormalMove(Square(1, 1), Square(1, 1), promote=False)


@pytest.mark.parametrize("kind", HAND_PIECE_KINDS)
def test_drop_move_valid(kind: PieceKind) -> None:
    """持ち駒7種類すべての打ち手を生成できる。"""
    move = DropMove(Square(1, 1), kind)

    assert move.kind == kind


def test_drop_move_king_invalid() -> None:
    """玉を打つ指し手を生成するとValueErrorになる。"""
    with pytest.raises(ValueError, match="玉を打つことはできません。"):
        DropMove(Square(1, 1), PieceKind.KING)


def test_square_equality_and_hash() -> None:
    """同じ座標のマスは等しく、辞書のキーとして使える。"""
    a = Square(1, 2)
    b = Square(1, 2)

    assert a == b
    assert {a: "test"}[b] == "test"


def test_normal_move_equality_and_hash() -> None:
    """同じ指し手は等しく、辞書のキーとして使える。"""
    a = NormalMove(Square(1, 1), Square(2, 2), promote=True)
    b = NormalMove(Square(1, 1), Square(2, 2), promote=True)

    assert a == b
    assert {a: "test"}[b] == "test"


def test_drop_move_equality_and_hash() -> None:
    """同じ打ち手は等しく、辞書のキーとして使える。"""
    a = DropMove(Square(1, 1), PieceKind.PAWN)
    b = DropMove(Square(1, 1), PieceKind.PAWN)

    assert a == b
    assert {a: "test"}[b] == "test"
