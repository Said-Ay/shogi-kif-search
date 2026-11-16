# Copyright (C) 2026 Said-Ay
# SPDX-License-Identifier: GPL-3.0-only

"""usi.pyのテスト。"""

import cshogi
import pytest

from shogi_kif_search.move import DropMove, Move, NormalMove, Square
from shogi_kif_search.piece import HAND_PIECE_KINDS, PieceKind
from shogi_kif_search.usi import parse_usi


@pytest.mark.parametrize(
    ("text", "expected"),
    [
        ("7g7f", NormalMove(Square(7, 7), Square(7, 6), promote=False)),
        ("8h2b+", NormalMove(Square(8, 8), Square(2, 2), promote=True)),
        ("2b8h", NormalMove(Square(2, 2), Square(8, 8), promote=False)),
        ("1a9i", NormalMove(Square(1, 1), Square(9, 9), promote=False)),
        ("9i1a+", NormalMove(Square(9, 9), Square(1, 1), promote=True)),
        ("P*5e", DropMove(Square(5, 5), PieceKind.PAWN)),
        ("R*1a", DropMove(Square(1, 1), PieceKind.ROOK)),
        ("N*9i", DropMove(Square(9, 9), PieceKind.KNIGHT)),
    ],
)
def test_parse_usi(text: str, expected: Move) -> None:
    """USI形式の指し手が、対応する指し手の型に変換されることを確認する。"""
    assert parse_usi(text) == expected


@pytest.mark.parametrize("kind", HAND_PIECE_KINDS)
def test_parse_usi_drop_all_kinds(kind: PieceKind) -> None:
    """持ち駒になる7種類すべてを打つ手に変換できることを確認する。"""
    assert parse_usi(f"{kind.value}*5e") == DropMove(Square(5, 5), kind)


@pytest.mark.parametrize(
    "text",
    [
        "",
        "7g7",
        "7g7f7",
        "7g7f-",
        "7g7f++",
        "0a1a",
        "7j7f",
        "7G7F",
        "７g７f",  # USIの筋は半角数字だけなので全角数字を渡すと ValueErrorになる
        "K*5e",
        "p*5e",
        "P*5",
        "P*0e",
        "P5e",
        " 7g7f",
        "7g7f ",
        "resign",
    ],
)
def test_parse_usi_invalid(text: str) -> None:
    """USI形式の指し手として読めない文字列はValueErrorになることを確認する。"""
    with pytest.raises(ValueError, match="USI形式の指し手として読めません。"):
        parse_usi(text)


def test_parse_usi_same_square() -> None:
    """移動元と移動先が同じ手はValueErrorになることを確認する。"""
    with pytest.raises(ValueError, match="同じマス目に移動できません。"):
        parse_usi("7g7g")


def test_parse_usi_initial_legal_moves() -> None:
    """cshogiが生成した初期局面の合法手を、すべて変換できることを確認する。"""
    board = cshogi.Board()
    for move in board.legal_moves:
        text = cshogi.move_to_usi(move)
        assert isinstance(parse_usi(text), NormalMove), text
