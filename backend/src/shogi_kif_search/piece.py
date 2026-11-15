# Copyright (C) 2026 Said-Ay
# SPDX-License-Identifier: GPL-3.0-only

"""駒の定義。"""

import enum
from dataclasses import dataclass

# 盤の大きさ。筋と段はどちらも1からBOARD_SIZEまで
BOARD_SIZE = 9


class Color(enum.Enum):
    """駒が先手後手どちらのものかを定義するクラス。"""

    BLACK = 0
    WHITE = 1


class PieceKind(enum.Enum):
    """駒の種類を定義するクラス。"""

    PAWN = "P"
    LANCE = "L"
    KNIGHT = "N"
    SILVER = "S"
    GOLD = "G"
    BISHOP = "B"
    ROOK = "R"
    KING = "K"


@dataclass(frozen=True)
class Piece:
    """駒の定義をするクラス。"""

    kind: PieceKind
    color: Color
    promoted: bool = False

    def __post_init__(self) -> None:
        """玉と金が成っていないかを確認する。"""
        if self.promoted and self.kind in [PieceKind.GOLD, PieceKind.KING]:
            msg = f"金と玉は成ることができません。kind: {self.kind}, promoted: {self.promoted}"
            raise ValueError(msg)


HAND_PIECE_KINDS = (
    PieceKind.ROOK,
    PieceKind.BISHOP,
    PieceKind.GOLD,
    PieceKind.SILVER,
    PieceKind.KNIGHT,
    PieceKind.LANCE,
    PieceKind.PAWN,
)
