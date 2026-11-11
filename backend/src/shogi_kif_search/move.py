# Copyright (C) 2026 Said-Ay
# SPDX-License-Identifier: GPL-3.0-only

"""指し手の型を定義する。"""

from dataclasses import dataclass

from shogi_kif_search.piece import BOARD_SIZE, PieceKind


@dataclass(frozen=True)
class Square:
    """将棋の盤上のマス目を表すクラス。"""

    file: int  # 筋、1から9までの整数
    rank: int  # 段、1から9までの整数

    def __post_init__(self) -> None:
        """マス目の妥当性を確認する。"""
        if not (1 <= self.file <= BOARD_SIZE):
            msg = f"筋は1から9までの整数でなければなりません。file: {self.file}"
            raise ValueError(msg)
        if not (1 <= self.rank <= BOARD_SIZE):
            msg = f"段は1から9までの整数でなければなりません。rank: {self.rank}"
            raise ValueError(msg)


@dataclass(frozen=True)
class NormalMove:
    """盤上の駒を動かす指し手を表すクラス。"""

    from_square: Square
    to_square: Square
    promote: bool

    def __post_init__(self) -> None:
        """指し手の妥当性を確認する。"""
        if self.from_square == self.to_square:
            msg = f"同じマス目に移動できません。from_square: {self.from_square}, to_square: {self.to_square}"
            raise ValueError(msg)


@dataclass(frozen=True)
class DropMove:
    """駒を打つ指し手を表すクラス。"""

    square: Square
    kind: PieceKind

    def __post_init__(self) -> None:
        """駒を打つ指し手の妥当性を確認する。"""
        if self.kind == PieceKind.KING:
            msg = f"玉を打つことはできません。kind: {self.kind}"
            raise ValueError(msg)


# 指し手。盤上の駒を動かす手(NormalMove)か、持ち駒を打つ手(DropMove)のどちらか。
# 移動元と打つ駒を両方持つ、または両方持たない指し手を作れないように、2つのクラスに分けている。
type Move = NormalMove | DropMove
