# Copyright (C) 2026 Said-Ay
# SPDX-License-Identifier: GPL-3.0-only

"""USI形式の指し手の文字列と、指し手の型を相互に変換する。"""

import re

from shogi_kif_search.move import DropMove, Move, NormalMove, Square
from shogi_kif_search.piece import PieceKind

# USIの段は a から i のアルファベットで、a が一段目になる
_RANKS = "abcdefghi"

# 盤上の駒を動かす手。例: 7g7f、8h2b+
_NORMAL_MOVE_PATTERN = re.compile(r"([1-9])([a-i])([1-9])([a-i])(\+?)")

# 持ち駒を打つ手。例: P*5e。玉は打てないので K は含めない
_DROP_MOVE_PATTERN = re.compile(r"([PLNSGBR])\*([1-9])([a-i])")


def parse_usi(text: str) -> Move:
    """USI形式の指し手の文字列を、指し手の型に変換する。

    局面は見ないので、空きマスから動かす手や持っていない駒を打つ手もそのまま変換する。
    それらは局面に適用するときに確かめる。

    Args:
        text: USI形式の指し手。例えば `7g7f`、`8h2b+`、`P*5e`。

    Returns:
        盤上の駒を動かす手なら `NormalMove`、持ち駒を打つ手なら `DropMove`。

    Raises:
        ValueError: USI形式の指し手として読めない場合、または移動元と移動先が同じ場合。
    """
    if normal := _NORMAL_MOVE_PATTERN.fullmatch(text):
        from_file, from_rank, to_file, to_rank, promote = normal.groups()
        return NormalMove(
            from_square=_parse_square(from_file, from_rank),
            to_square=_parse_square(to_file, to_rank),
            promote=promote == "+",
        )
    if drop := _DROP_MOVE_PATTERN.fullmatch(text):
        kind, to_file, to_rank = drop.groups()
        return DropMove(square=_parse_square(to_file, to_rank), kind=PieceKind(kind))
    msg = f"USI形式の指し手として読めません。text: {text!r}"
    raise ValueError(msg)


def to_usi(move: Move) -> str:
    """指し手の型を、USI形式の指し手の文字列に変換する。`parse_usi` の逆。

    Args:
        move: 指し手。

    Returns:
        USI形式の指し手。例えば `7g7f`、`8h2b+`、`P*5e`。
    """
    if isinstance(move, NormalMove):
        promote = "+" if move.promote else ""
        return f"{_square_to_usi(move.from_square)}{_square_to_usi(move.to_square)}{promote}"
    return f"{move.kind.value}*{_square_to_usi(move.square)}"


def _square_to_usi(square: Square) -> str:
    """マス目を、USIの筋の数字と段のアルファベットに変換する。"""
    return f"{square.file}{_RANKS[square.rank - 1]}"


def _parse_square(file_char: str, rank_char: str) -> Square:
    """USIの筋の数字と段のアルファベットを、マス目に変換する。

    Args:
        file_char: 筋。`1` から `9` の数字。
        rank_char: 段。`a` から `i` のアルファベット。

    Returns:
        マス目。
    """
    return Square(file=int(file_char), rank=_RANKS.index(rank_char) + 1)
