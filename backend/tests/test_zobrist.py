# Copyright (C) 2026 Said-Ay
# SPDX-License-Identifier: GPL-3.0-only

"""Zobrist Hashのテスト。"""

import cshogi
from hypothesis import given, settings
from hypothesis import strategies as st

from shogi_kif_search.piece import BOARD_SIZE, Color, Piece, PieceKind
from shogi_kif_search.position import Position
from shogi_kif_search.usi import parse_usi
from shogi_kif_search.zobrist import calculate_hash, update_hash

# テストベクトル:平手初期局面のハッシュ値。改変禁止
INITIAL_POSITION_HASH = 0x216B53C6C9D64459
EXPECTED_HAND_HASH = 0x71295E06A1E9BBF1


@settings(max_examples=30, deadline=None)
@given(st.data())
def test_update_hash_matches_calculate_hash(data: st.DataObject) -> None:
    """ランダムな合法手で、差分更新と一括計算が一致することを確認する。"""
    position = Position.initial()
    board = cshogi.Board()

    hash_value = calculate_hash(position)

    for _ in range(100):
        legal_moves = list(board.legal_moves)

        if not legal_moves:
            break

        cshogi_move = data.draw(st.sampled_from(legal_moves))
        move = parse_usi(cshogi.move_to_usi(cshogi_move))

        new_hash = update_hash(hash_value, position, move)

        position.push(move)
        hash_value = new_hash

        assert hash_value == calculate_hash(position)

        board.push(cshogi_move)


def test_initial_hash() -> None:
    """平手の初期局面のハッシュ値が固定値と一致することを確認する。"""
    assert calculate_hash(Position.initial()) == INITIAL_POSITION_HASH


def test_hand_hash() -> None:
    """持ち駒を含む局面のハッシュ値が固定値と一致することを確認する。"""
    board: list[list[Piece | None]] = [[None for _ in range(9)] for _ in range(BOARD_SIZE)]

    board[0][4] = Piece(PieceKind.KING, Color.WHITE)
    board[8][4] = Piece(PieceKind.KING, Color.BLACK)

    hands = {
        Color.BLACK: {PieceKind.PAWN: 2},
        Color.WHITE: {PieceKind.BISHOP: 1},
    }

    position = Position(
        board=board,
        hands=hands,
        turn=Color.BLACK,
        move_number=1,
    )
    assert calculate_hash(position) == EXPECTED_HAND_HASH
