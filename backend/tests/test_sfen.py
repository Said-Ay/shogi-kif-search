# Copyright (C) 2026 Said-Ay
# SPDX-License-Identifier: GPL-3.0-only

"""sfen.pyのテスト。

盤面・手番・手数の書き方は、test_position.py で毎手の局面を cshogi と比べることでも確かめている。
"""

import cshogi
import pytest

from shogi_kif_search.piece import Color, PieceKind
from shogi_kif_search.position import Position
from shogi_kif_search.sfen import to_sfen


def test_initial_sfen() -> None:
    """平手の初期局面のSFENがcshogiと一致することを確認する。"""
    assert to_sfen(Position.initial()) == cshogi.Board().sfen()


@pytest.mark.parametrize(
    ("hands", "expected"),
    [
        (
            {
                Color.BLACK: {PieceKind.ROOK: 1, PieceKind.BISHOP: 1, PieceKind.PAWN: 2},
                Color.WHITE: {PieceKind.ROOK: 1, PieceKind.BISHOP: 1, PieceKind.PAWN: 3},
            },
            "RB2Prb3p",
        ),
        ({Color.BLACK: {PieceKind.PAWN: 18}}, "18P"),
    ],
)
def test_hands_sfen(hands: dict[Color, dict[PieceKind, int]], expected: str) -> None:
    """持ち駒が先手・後手の順、飛角金銀桂香歩の順に並び、2枚以上なら枚数が付くことを確認する。"""
    position = Position(board=[[None] * 9 for _ in range(9)], hands=hands, turn=Color.BLACK, move_number=1)
    assert to_sfen(position).split()[2] == expected
