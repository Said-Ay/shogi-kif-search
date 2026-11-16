# Copyright (C) 2026 Said-Ay
# SPDX-License-Identifier: GPL-3.0-only

"""KIF形式の指し手の文字列を、指し手の型に変換する。"""

import re

from shogi_kif_search.move import DropMove, Move, NormalMove, Square
from shogi_kif_search.piece import PieceKind

# 移動先の筋は全角数字、段は漢数字で書く
_FILES = "１２３４５６７８９"
_RANKS = "一二三四五六七八九"

# 盤上の駒の名前。成銀・成桂・成香も1つの駒の名前として読み、
# その後ろの「成」とは区別する。玉と王、龍と竜、成銀と全、成桂と圭、成香と杏は同じ駒
_BOARD_PIECE_NAMES = "成銀|成桂|成香|歩|香|桂|銀|金|角|飛|玉|王|と|全|圭|杏|馬|龍|竜"

# 持ち駒として打てる駒の名前と、その種類
_DROP_PIECE_KINDS = {
    "歩": PieceKind.PAWN,
    "香": PieceKind.LANCE,
    "桂": PieceKind.KNIGHT,
    "銀": PieceKind.SILVER,
    "金": PieceKind.GOLD,
    "角": PieceKind.BISHOP,
    "飛": PieceKind.ROOK,
}

# 盤上の駒を動かす手。例: ７六歩(77)、２二角成(88)、２二成銀(31)、同　歩(23)
# 移動先は、マス目か、直前の指し手と同じマスを表す「同」で書く。「同」の後の全角空白はないこともある
_NORMAL_MOVE_PATTERN = re.compile(
    rf"(?:([{_FILES}])([{_RANKS}])|同　?)(?:{_BOARD_PIECE_NAMES})(成?)\(([1-9])([1-9])\)"
)

# 持ち駒を打つ手。例: ５五角打
_DROP_MOVE_PATTERN = re.compile(rf"([{_FILES}])([{_RANKS}])({'|'.join(_DROP_PIECE_KINDS)})打")


def parse_kif_move(text: str, previous_to: Square | None = None) -> Move:
    """KIF形式の指し手の部分を、指し手の型に変換する。

    手数や消費時間を含まない、指し手の部分だけを受け取る。
    駒の名前の後ろに「成」があれば成る手とし、成銀などの駒の名前に含まれる「成」とは区別する。
    盤上の駒を動かす手では、駒の名前は確かめるだけで残さず、盤面の駒と一致するかも確かめない。
    「同」は、直前の指し手の移動先を移動先とする。

    Args:
        text: KIF形式の指し手の部分。例えば `７六歩(77)`、`２二角成(88)`、`５五角打`、`同　歩(23)`。
        previous_to: 直前の指し手の移動先。「同」を解釈するときだけ使う。初手では `None`。

    Returns:
        盤上の駒を動かす手なら `NormalMove`、持ち駒を打つ手なら `DropMove`。

    Raises:
        ValueError: KIF形式の指し手として読めない場合、`不成` と書かれている場合、
            直前の指し手がないのに「同」と書かれている場合、または移動元と移動先が同じ場合。
    """
    if normal := _NORMAL_MOVE_PATTERN.fullmatch(text):
        to_file, to_rank, promote, from_file, from_rank = normal.groups()
        if to_file is not None:
            to_square = _parse_square(to_file, to_rank)
        elif previous_to is not None:
            to_square = previous_to
        else:
            msg = f"直前の指し手がないので「同」を解釈できません。text: {text!r}"
            raise ValueError(msg)
        return NormalMove(
            from_square=Square(file=int(from_file), rank=int(from_rank)),
            to_square=to_square,
            promote=promote == "成",
        )
    if drop := _DROP_MOVE_PATTERN.fullmatch(text):
        to_file, to_rank, name = drop.groups()
        return DropMove(square=_parse_square(to_file, to_rank), kind=_DROP_PIECE_KINDS[name])
    if "不成" in text:
        msg = f"KIFの仕様に「不成」はありません。成らない手は「成」を書きません。text: {text!r}"
        raise ValueError(msg)
    msg = f"KIF形式の指し手として読めません。text: {text!r}"
    raise ValueError(msg)


def _parse_square(file_char: str, rank_char: str) -> Square:
    """KIFの筋の全角数字と段の漢数字を、マス目に変換する。

    Args:
        file_char: 筋。`１` から `９` の全角数字。
        rank_char: 段。`一` から `九` の漢数字。

    Returns:
        マス目。
    """
    return Square(file=_FILES.index(file_char) + 1, rank=_RANKS.index(rank_char) + 1)
