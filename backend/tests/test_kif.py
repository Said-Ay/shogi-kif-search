# Copyright (C) 2026 Said-Ay
# SPDX-License-Identifier: GPL-3.0-only

"""kif.pyのテスト。"""

import pytest

from shogi_kif_search.kif import parse_kif_move
from shogi_kif_search.move import DropMove, Move, NormalMove, Square
from shogi_kif_search.piece import PieceKind


@pytest.mark.parametrize(
    ("text", "expected"),
    [
        ("７六歩(77)", NormalMove(Square(7, 7), Square(7, 6), promote=False)),
        ("２二角成(88)", NormalMove(Square(8, 8), Square(2, 2), promote=True)),
        ("５五角打", DropMove(Square(5, 5), PieceKind.BISHOP)),
    ],
)
def test_parse_kif_move(text: str, expected: Move) -> None:
    """KIF形式の指し手が、対応する指し手の型に変換されることを確認する。"""
    assert parse_kif_move(text) == expected


@pytest.mark.parametrize(
    ("text", "promote"),
    [("２二銀成(31)", True), ("２二成銀(31)", False), ("９二馬(91)", False)],
)
def test_parse_kif_move_promote(text: str, *, promote: bool) -> None:
    """駒の名前の後ろの「成」だけを成る手とし、成銀などの駒の名前とは区別することを確認する。"""
    move = parse_kif_move(text)
    assert isinstance(move, NormalMove)
    assert move.promote is promote


def test_parse_kif_move_alias() -> None:
    """同じ駒の別の書き方が、同じ指し手に変換されることを確認する。"""
    assert parse_kif_move("２二成銀(31)") == parse_kif_move("２二全(31)")


@pytest.mark.parametrize(
    ("text", "message"),
    [
        ("２二銀不成(31)", "KIFの仕様に「不成」はありません。"),
        ("７六歩", "KIF形式の指し手として読めません。"),
    ],
)
def test_parse_kif_move_invalid(text: str, message: str) -> None:
    """不成と、KIF形式の指し手として読めない文字列はValueErrorになることを確認する。"""
    with pytest.raises(ValueError, match=message):
        parse_kif_move(text)
