# Copyright (C) 2026 Said-Ay
# SPDX-License-Identifier: GPL-3.0-only

"""局面をSFEN形式に変換する関数バックエンドライブラリ。"""

from typing import TYPE_CHECKING

from shogi_kif_search.piece import HAND_PIECE_KINDS, Color

if TYPE_CHECKING:
    from shogi_kif_search.piece import Piece, PieceKind
    from shogi_kif_search.position import Position


def piece_to_sfen(piece: Piece) -> str:
    """駒をSFEN形式の文字列に変換する。"""
    sfen_piece = piece.kind.value
    if piece.color == Color.WHITE:
        sfen_piece = sfen_piece.lower()
    if piece.promoted:
        sfen_piece = "+" + sfen_piece
    return sfen_piece


def board_to_sfen(board: list[list[Piece | None]]) -> str:
    """盤面をSFEN形式の文字列に変換する。"""
    sfen_rows = []
    for row in board:
        empty_count = 0
        sfen_row = ""
        for piece in row:
            if piece is None:
                empty_count += 1
            else:
                if empty_count > 0:
                    sfen_row += str(empty_count)
                    empty_count = 0
                sfen_row += piece_to_sfen(piece)
        if empty_count > 0:
            sfen_row += str(empty_count)
        sfen_rows.append(sfen_row)
    return "/".join(sfen_rows)


def hands_to_sfen(hands: dict[Color, dict[PieceKind, int]]) -> str:
    """持ち駒をSFEN形式の文字列に変換する。"""
    sfen_hands = []

    for color in Color:
        for kind in HAND_PIECE_KINDS:
            count = hands.get(color, {}).get(kind, 0)

            if count == 0:
                continue

            symbol = kind.value

            if color == Color.WHITE:
                symbol = symbol.lower()

            if count > 1:
                sfen_hands.append(f"{count}{symbol}")
            else:
                sfen_hands.append(symbol)

    return "".join(sfen_hands) if sfen_hands else "-"


def to_sfen(position: Position) -> str:
    """局面をSFEN形式の文字列に変換する。"""
    board_sfen = board_to_sfen(position.board)  # 盤面の変換
    turn_sfen = "b" if position.turn == Color.BLACK else "w"  # b または w
    hands_sfen = hands_to_sfen(position.hands)  # 持ち駒
    move_number = str(position.move_number)  # 手数

    return f"{board_sfen} {turn_sfen} {hands_sfen} {move_number}"
