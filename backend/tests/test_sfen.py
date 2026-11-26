# Copyright (C) 2026 Said-Ay
# SPDX-License-Identifier: GPL-3.0-only

"""sfen.pyのテスト。

盤面・手番・手数の書き方は、test_position.py で毎手の局面を cshogi と比べることでも確かめている。
"""

import cshogi
import pytest

from shogi_kif_search.piece import BOARD_SIZE, Color, PieceKind
from shogi_kif_search.position import Position
from shogi_kif_search.sfen import strip_move_number, to_sfen


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
    position = Position(
        board=[[None] * BOARD_SIZE for _ in range(BOARD_SIZE)], hands=hands, turn=Color.BLACK, move_number=1
    )
    assert to_sfen(position).split()[2] == expected


def test_strip_move_number() -> None:
    """SFENから手数だけが除かれることを確認する。"""
    sfen = "lnsgkgsnl/1r5b1/ppppppppp/9/9/9/PPPPPPPPP/1B5R1/LNSGKGSNL b - 1"
    assert strip_move_number(sfen) == "lnsgkgsnl/1r5b1/ppppppppp/9/9/9/PPPPPPPPP/1B5R1/LNSGKGSNL b -"


def test_strip_move_number_invalid() -> None:
    """手数がないSFENはValueErrorになることを確認する。"""
    with pytest.raises(ValueError, match="SFENは盤面・手番・持ち駒・手数の4つを空白でつなぎます。"):
        strip_move_number("lnsgkgsnl/1r5b1/ppppppppp/9/9/9/PPPPPPPPP/1B5R1/LNSGKGSNL b -")
