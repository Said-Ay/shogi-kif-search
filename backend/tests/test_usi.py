# Copyright (C) 2026 Said-Ay
# SPDX-License-Identifier: GPL-3.0-only

"""usi.pyのテスト。"""

import pytest

from shogi_kif_search.move import DropMove, Move, NormalMove, Square
from shogi_kif_search.piece import PieceKind
from shogi_kif_search.usi import parse_usi


@pytest.mark.parametrize(
    ("text", "expected"),
    [
        ("7g7f", NormalMove(Square(7, 7), Square(7, 6), promote=False)),
        ("8h2b+", NormalMove(Square(8, 8), Square(2, 2), promote=True)),
        ("P*5e", DropMove(Square(5, 5), PieceKind.PAWN)),
    ],
)
def test_parse_usi(text: str, expected: Move) -> None:
    """USI形式の指し手が、対応する指し手の型に変換されることを確認する。"""
    assert parse_usi(text) == expected


@pytest.mark.parametrize("text", ["7g7f7", "K*5e", "resign"])
def test_parse_usi_invalid(text: str) -> None:
    """USI形式の指し手として読めない文字列はValueErrorになることを確認する。"""
    with pytest.raises(ValueError, match="USI形式の指し手として読めません。"):
        parse_usi(text)
