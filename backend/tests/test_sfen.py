# Copyright (C) 2026 Said-Ay
# SPDX-License-Identifier: GPL-3.0-only

"""sfen.pyのテスト。"""

import cshogi
import pytest

from shogi_kif_search.piece import Color, Piece, PieceKind
from shogi_kif_search.position import Position
from shogi_kif_search.sfen import to_sfen


def test_initial_sfen() -> None:
    """初期局面のSFENが正しいことを確認する。"""
    assert to_sfen(Position.initial()) == cshogi.Board().sfen()


@pytest.mark.parametrize(
    ("hands", "sfen"),
    [
        ({}, "-"),
        ({Color.BLACK: {PieceKind.PAWN: 1}, Color.WHITE: {PieceKind.PAWN: 1}}, "Pp"),
        (
            {
                Color.BLACK: {PieceKind.ROOK: 1, PieceKind.BISHOP: 1, PieceKind.PAWN: 2},
                Color.WHITE: {PieceKind.ROOK: 1, PieceKind.BISHOP: 1, PieceKind.PAWN: 3},
            },
            "RB2Prb3p",
        ),
        (
            {
                Color.WHITE: {
                    PieceKind.ROOK: 1,
                    PieceKind.BISHOP: 1,
                    PieceKind.GOLD: 1,
                    PieceKind.SILVER: 1,
                    PieceKind.KNIGHT: 1,
                    PieceKind.LANCE: 1,
                    PieceKind.PAWN: 1,
                }
            },
            "rbgsnlp",
        ),
        ({Color.BLACK: {PieceKind.PAWN: 18}}, "18P"),
    ],
)
def test_hands_to_sfen(hands: dict[Color, dict[PieceKind, int]], sfen: str) -> None:
    """持ち駒のSFENが正しいことを確認する。"""
    position = Position(
        board=[[None] * 9 for _ in range(9)],
        hands=hands,
        turn=Color.BLACK,
        move_number=1,
    )
    assert to_sfen(position).split()[2] == sfen


def test_promoted_pieces() -> None:
    """成り駒と空きマスを含む盤面のSFENを確認する。"""
    board: list[list[Piece | None]] = [[None] * 9 for _ in range(9)]

    board[0][0] = Piece(
        kind=PieceKind.PAWN,
        color=Color.BLACK,
        promoted=True,
    )

    board[0][8] = Piece(
        kind=PieceKind.ROOK,
        color=Color.WHITE,
        promoted=True,
    )

    position = Position(
        board=board,
        hands={},
        turn=Color.BLACK,
        move_number=1,
    )

    assert to_sfen(position).split()[0] == "+P7+r/9/9/9/9/9/9/9/9"


def test_turn_and_move_number() -> None:
    """後手番と2桁の手数が正しく出力されることを確認する。"""
    position = Position(
        board=[[None] * 9 for _ in range(9)],
        hands={},
        turn=Color.WHITE,
        move_number=25,
    )

    assert to_sfen(position).split()[1] == "w"
    assert to_sfen(position).split()[3] == "25"
