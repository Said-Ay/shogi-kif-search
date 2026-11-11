# Copyright (C) 2026 Said-Ay
# SPDX-License-Identifier: GPL-3.0-only

"""position.pyのテスト。"""

import pytest

from shogi_kif_search.move import Square
from shogi_kif_search.piece import HAND_PIECE_KINDS, Color, Piece, PieceKind
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


@pytest.mark.parametrize(
    ("file_num", "rank_num", "expected"),
    [
        (2, 2, (1, 7)),
        (8, 2, (1, 1)),
        (2, 8, (7, 7)),
        (9, 1, (0, 0)),
        (1, 1, (0, 8)),
        (9, 9, (8, 0)),
        (1, 9, (8, 8)),
        (5, 5, (4, 4)),
    ],
)
def test_square_to_index(file_num: int, rank_num: int, expected: tuple[int, int]) -> None:
    """square_to_index()がマス目を盤面のインデックスに変換することを確認する。"""
    assert Position.square_to_index(Square(file_num, rank_num)) == expected


def test_initial() -> None:
    """initial()で初期局面が正しく生成されることを確認する。"""
    position = Position.initial()

    b = Color.BLACK
    w = Color.WHITE
    k = PieceKind

    expected_board = [
        [
            Piece(kind, w)
            for kind in (
                k.LANCE,
                k.KNIGHT,
                k.SILVER,
                k.GOLD,
                k.KING,
                k.GOLD,
                k.SILVER,
                k.KNIGHT,
                k.LANCE,
            )
        ],
        [None, Piece(k.ROOK, w), None, None, None, None, None, Piece(k.BISHOP, w), None],
        [Piece(k.PAWN, w)] * 9,
        [None] * 9,
        [None] * 9,
        [None] * 9,
        [Piece(k.PAWN, b)] * 9,
        [None, Piece(k.BISHOP, b), None, None, None, None, None, Piece(k.ROOK, b), None],
        [
            Piece(kind, b)
            for kind in (
                k.LANCE,
                k.KNIGHT,
                k.SILVER,
                k.GOLD,
                k.KING,
                k.GOLD,
                k.SILVER,
                k.KNIGHT,
                k.LANCE,
            )
        ],
    ]

    assert position.board == expected_board
    assert position.turn == Color.BLACK
    assert position.hands == {
        Color.BLACK: dict.fromkeys(HAND_PIECE_KINDS, 0),
        Color.WHITE: dict.fromkeys(HAND_PIECE_KINDS, 0),
    }
    assert position.move_number == 1
