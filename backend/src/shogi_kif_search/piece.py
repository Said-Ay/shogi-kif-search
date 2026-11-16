# Copyright (C) 2026 Said-Ay
# SPDX-License-Identifier: GPL-3.0-only

"""駒と、盤の大きさを定義する。"""

import enum
from dataclasses import dataclass

# 盤の大きさ。筋と段はどちらも1からBOARD_SIZEまで
BOARD_SIZE = 9


class Color(enum.Enum):
    """先手と後手。"""

    BLACK = 0
    WHITE = 1

    @property
    def opponent(self) -> Color:
        """相手側。先手なら後手、後手なら先手。"""
        return Color.WHITE if self is Color.BLACK else Color.BLACK


class PieceKind(enum.Enum):
    """駒の種類。値はSFENとUSIで使う大文字の1文字。"""

    PAWN = "P"
    LANCE = "L"
    KNIGHT = "N"
    SILVER = "S"
    GOLD = "G"
    BISHOP = "B"
    ROOK = "R"
    KING = "K"


# 成れない駒の種類
_UNPROMOTABLE_KINDS = frozenset({PieceKind.GOLD, PieceKind.KING})


@dataclass(frozen=True)
class Piece:
    """盤上の駒。種類、先後、成っているかを持つ。"""

    kind: PieceKind
    color: Color
    promoted: bool = False

    def __post_init__(self) -> None:
        """成れない駒が成っていないかを確かめる。

        Raises:
            ValueError: 金か玉が成っている場合。
        """
        if self.promoted and self.kind in _UNPROMOTABLE_KINDS:
            msg = f"金と玉は成れません。kind: {self.kind}"
            raise ValueError(msg)


# 持ち駒になる駒の種類。SFENで持ち駒を書く順番に並べている
HAND_PIECE_KINDS = (
    PieceKind.ROOK,
    PieceKind.BISHOP,
    PieceKind.GOLD,
    PieceKind.SILVER,
    PieceKind.KNIGHT,
    PieceKind.LANCE,
    PieceKind.PAWN,
)
