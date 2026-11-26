# Copyright (C) 2026 Said-Ay
# SPDX-License-Identifier: GPL-3.0-only

"""局面をSFEN形式の文字列に変換する。"""

from typing import TYPE_CHECKING

from shogi_kif_search.piece import HAND_PIECE_KINDS, Color

if TYPE_CHECKING:
    from collections.abc import Mapping, Sequence

    from shogi_kif_search.piece import Piece, PieceKind
    from shogi_kif_search.position import Position


# SFENを空白で区切った部分の数。盤面、手番、持ち駒、手数
_SFEN_PARTS = 4


def to_sfen(position: Position) -> str:
    """局面をSFEN形式の文字列に変換する。

    盤面、手番、持ち駒、手数の4つを空白でつなぐ。

    Args:
        position: 局面。

    Returns:
        SFEN形式の文字列。例えば平手の初期局面なら
        `lnsgkgsnl/1r5b1/ppppppppp/9/9/9/PPPPPPPPP/1B5R1/LNSGKGSNL b - 1`。
    """
    turn = "b" if position.turn is Color.BLACK else "w"
    return f"{_board_to_sfen(position.board)} {turn} {_hands_to_sfen(position.hands)} {position.move_number}"


def strip_move_number(sfen: str) -> str:
    """SFEN形式の文字列から、最後の手数を除く。

    手数だけが違う局面を同じ局面として扱うために使う。

    Args:
        sfen: 盤面、手番、持ち駒、手数の4つを空白でつないだSFEN形式の文字列。

    Returns:
        盤面、手番、持ち駒の3つを空白でつないだ文字列。
    """
    parts = sfen.split(" ")
    if len(parts) != _SFEN_PARTS:
        msg = f"SFENは盤面・手番・持ち駒・手数の{_SFEN_PARTS}つを空白でつなぎます。sfen: {sfen!r}"
        raise ValueError(msg)
    return " ".join(parts[:-1])


def _letter(kind: PieceKind, color: Color) -> str:
    """駒の種類を表す1文字。先手は大文字、後手は小文字にする。"""
    return kind.value if color is Color.BLACK else kind.value.lower()


def _piece_to_sfen(piece: Piece) -> str:
    """盤上の駒を、SFEN形式の文字列に変換する。成り駒は前に `+` を付ける。"""
    letter = _letter(piece.kind, piece.color)
    return f"+{letter}" if piece.promoted else letter


def _board_to_sfen(board: Sequence[Sequence[Piece | None]]) -> str:
    """盤面をSFEN形式の文字列に変換する。連続する空きマスは数字にまとめる。"""
    rows = []
    for row in board:
        text = ""
        empty_count = 0
        for piece in row:
            if piece is None:
                empty_count += 1
                continue
            if empty_count > 0:
                text += str(empty_count)
                empty_count = 0
            text += _piece_to_sfen(piece)
        if empty_count > 0:
            text += str(empty_count)
        rows.append(text)
    return "/".join(rows)


def _hands_to_sfen(hands: Mapping[Color, Mapping[PieceKind, int]]) -> str:
    """持ち駒をSFEN形式の文字列に変換する。

    先手、後手の順に、飛角金銀桂香歩の順で並べる。2枚以上なら前に枚数を付け、持ち駒がなければ `-` にする。
    """
    parts = []
    for color in Color:
        for kind in HAND_PIECE_KINDS:
            count = hands[color][kind]
            if count == 0:
                continue
            prefix = str(count) if count > 1 else ""
            parts.append(f"{prefix}{_letter(kind, color)}")
    return "".join(parts) or "-"
