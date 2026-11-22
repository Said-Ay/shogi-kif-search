# Copyright (C) 2026 Said-Ay
# SPDX-License-Identifier: GPL-3.0-only

"""局面のZobristハッシュを計算する。"""

import hashlib
from typing import TYPE_CHECKING

from shogi_kif_search.move import NormalMove, Square
from shogi_kif_search.piece import Color, Piece, PieceKind

if TYPE_CHECKING:
    from shogi_kif_search.move import Move
    from shogi_kif_search.position import Position


def _make_key(text: str) -> int:
    """文字列から64ビットのハッシュ値を生成する。"""
    digest = hashlib.sha256(text.encode("ascii")).digest()
    return int.from_bytes(digest[:8], byteorder="big")


def _piece_code(piece: Piece) -> str:
    """駒をSFEN形式の文字列に変換する。"""
    code = piece.kind.value

    if piece.color is Color.WHITE:
        code = code.lower()

    if piece.promoted:
        code = "+" + code

    return code


def _square_code(square: Square) -> str:
    """マスを筋と段の数字に変換する。"""
    return f"{square.file}{square.rank}"


def _board_key(piece: Piece, square: Square) -> int:
    """盤上の駒と位置からハッシュ値を生成する。"""
    piece_code = _piece_code(piece)
    square_code = _square_code(square)

    return _make_key(f"zobrist-v1|board|{piece_code}|{square_code}")


def _hand_key(kind: PieceKind, color: Color, count: int) -> int:
    """持ち駒の駒種・先後・枚数に対応するキーを生成する。

    持ち駒が0枚の場合はハッシュに寄与しない。
    """
    if count == 0:
        return 0

    piece = Piece(
        kind=kind,
        color=color,
        promoted=False,
    )
    piece_code = _piece_code(piece)

    return _make_key(f"zobrist-v1|hand|{piece_code}|{count}")


_TURN_KEY = _make_key("zobrist-v1|turn")


def calculate_hash(position: Position) -> int:
    """局面の盤上の駒・持ち駒・手番からZobristハッシュを計算する。

    盤上にある各駒と、0枚でない持ち駒の枚数に対応するキーを
    XORしてハッシュを計算する。
    後手番の場合のみ、手番のキーを追加する。
    """
    hash_value = 0
    for y, row in enumerate(position.board):
        for x, piece in enumerate(row):
            if piece is None:
                continue

            square = position.index_to_square(y, x)
            hash_value ^= _board_key(piece, square)

    for color, hand in position.hands.items():
        for kind, count in hand.items():
            hash_value ^= _hand_key(kind, color, count)

    if position.turn is Color.WHITE:
        hash_value ^= _TURN_KEY

    return hash_value


def update_hash(old_hash: int, position: Position, move: Move) -> int:
    """指し手を適用した後のZobristハッシュを差分計算する。

    1. 移動元の駒を取り除く。
    2. 移動先に駒があれば取り除く。
    3. 駒取りの場合は、持ち駒の枚数を1枚増やす。
    4. 移動先に駒を置く。成る場合は成った後の駒を使う。
    5. 手番のキーをXORする。
    """
    hash_value = old_hash

    if isinstance(move, NormalMove):
        from_y, from_x = position.square_to_index(move.from_square)
        to_y, to_x = position.square_to_index(move.to_square)

        moved_piece = position.board[from_y][from_x]
        captured_piece = position.board[to_y][to_x]

        if moved_piece is None:
            msg = "移動元に駒がありません。"
            raise ValueError(msg)

        hash_value ^= _board_key(moved_piece, move.from_square)

        if captured_piece is not None:
            hash_value ^= _board_key(captured_piece, move.to_square)

            kind = captured_piece.kind
            color = position.turn
            count = position.hands[color][kind]

            hash_value ^= _hand_key(kind, color, count)
            hash_value ^= _hand_key(kind, color, count + 1)

        if move.promote:
            moved_piece = Piece(
                kind=moved_piece.kind,
                color=moved_piece.color,
                promoted=True,
            )

        hash_value ^= _board_key(moved_piece, move.to_square)

    else:  # DropMoveの場合
        kind = move.kind
        color = position.turn
        count = position.hands[color][kind]

        if count == 0:
            msg = "持ち駒がありません。"
            raise ValueError(msg)

        hash_value ^= _hand_key(kind, color, count)
        hash_value ^= _hand_key(kind, color, count - 1)

        dropped_piece = Piece(
            kind=kind,
            color=color,
            promoted=False,
        )
        hash_value ^= _board_key(dropped_piece, move.square)

    hash_value ^= _TURN_KEY

    return hash_value
