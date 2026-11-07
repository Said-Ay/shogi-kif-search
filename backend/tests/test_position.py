# Copyright (C) 2026 Said-Ay
# SPDX-License-Identifier: GPL-3.0-only

"""position.pyのテスト。"""

import pytest

from shogi_kif_search.piece import Color, Piece, PieceKind
from shogi_kif_search.position import Position


def test_invalid_board() -> None:
    """盤面が9行9列でない場合にValueErrorが発生することを確認する。"""
    invalid_board = [[None] * 9] * 8
    with pytest.raises(ValueError, match="盤面のサイズが異なります。"):
        Position(board=invalid_board, hands={}, turn=Color.BLACK, move_number=1)


def test_hands_complementation() -> None:
    """持ち駒の不足分が0で補完されることを確認する。"""
    hands = {Color.BLACK: {PieceKind.ROOK: 1}}

    position = Position(
        board=[[None] * 9 for _ in range(9)],
        hands=hands,
        turn=Color.BLACK,
        move_number=1,
    )

    expected_black = {
        PieceKind.ROOK: 1,
        PieceKind.BISHOP: 0,
        PieceKind.GOLD: 0,
        PieceKind.SILVER: 0,
        PieceKind.KNIGHT: 0,
        PieceKind.LANCE: 0,
        PieceKind.PAWN: 0,
    }
    expected_white = {
        PieceKind.ROOK: 0,
        PieceKind.BISHOP: 0,
        PieceKind.GOLD: 0,
        PieceKind.SILVER: 0,
        PieceKind.KNIGHT: 0,
        PieceKind.LANCE: 0,
        PieceKind.PAWN: 0,
    }
    assert position.hands == {
        Color.BLACK: expected_black,
        Color.WHITE: expected_white,
    }


def test_negative_hand_count() -> None:
    """持ち駒の枚数が負の場合にValueErrorが発生することを確認する。"""
    hands = {Color.BLACK: {PieceKind.ROOK: -1}}
    with pytest.raises(ValueError, match="持ち駒の枚数が負です。"):
        Position(
            board=[[None] * 9 for _ in range(9)],
            hands=hands,
            turn=Color.BLACK,
            move_number=1,
        )


def test_king_in_hands() -> None:
    """持ち駒に玉がある場合にValueErrorが発生することを確認する。"""
    hands = {Color.BLACK: {PieceKind.KING: 1}}
    with pytest.raises(ValueError, match="持ち駒に玉があることはありません。"):
        Position(
            board=[[None] * 9 for _ in range(9)],
            hands=hands,
            turn=Color.BLACK,
            move_number=1,
        )


def test_hands_copy() -> None:
    """元の持ち駒を変更しても局面が変化しないことを確認する。"""
    pawn_count = 2
    original_hands = {Color.BLACK: {PieceKind.PAWN: pawn_count}}

    position = Position(
        board=[[None] * 9 for _ in range(9)],
        hands=original_hands,
        turn=Color.BLACK,
        move_number=1,
    )

    # Position を生成した後、元の辞書を書き換える
    original_hands[Color.BLACK][PieceKind.PAWN] = 5

    # Position 内部の値は変わっていないはず
    assert position.hands[Color.BLACK][PieceKind.PAWN] == pawn_count


def test_board_copy() -> None:
    """元の盤面を変更しても局面の盤面が変わらないことを確認する。"""
    original_board: list[list[Piece | None]] = [[None] * 9 for _ in range(9)]

    position = Position(
        board=original_board,
        hands={},
        turn=Color.BLACK,
        move_number=1,
    )

    # Position の生成後に、元の盤面を変更する
    original_board[0][0] = Piece(
        kind=PieceKind.ROOK,
        color=Color.WHITE,
    )

    # Position 内部の盤面は変更されない
    assert position.board[0][0] is None
