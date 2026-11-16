# Copyright (C) 2026 Said-Ay
# SPDX-License-Identifier: GPL-3.0-only

"""マス目と指し手を定義する。"""

from dataclasses import dataclass

from shogi_kif_search.piece import BOARD_SIZE, PieceKind


@dataclass(frozen=True)
class Square:
    """盤上のマス目。

    Attributes:
        file: 筋。1から9。
        rank: 段。1から9。
    """

    file: int
    rank: int

    def __post_init__(self) -> None:
        """筋と段が盤の範囲内かを確かめる。

        Raises:
            ValueError: 筋か段が1から9の範囲外の場合。
        """
        if not (1 <= self.file <= BOARD_SIZE):
            msg = f"筋は1から{BOARD_SIZE}の整数です。file: {self.file}"
            raise ValueError(msg)
        if not (1 <= self.rank <= BOARD_SIZE):
            msg = f"段は1から{BOARD_SIZE}の整数です。rank: {self.rank}"
            raise ValueError(msg)


@dataclass(frozen=True)
class NormalMove:
    """盤上の駒を動かす指し手。"""

    from_square: Square
    to_square: Square
    promote: bool

    def __post_init__(self) -> None:
        """移動元と移動先が違うかを確かめる。

        Raises:
            ValueError: 移動元と移動先が同じ場合。
        """
        if self.from_square == self.to_square:
            msg = f"同じマス目に移動できません。square: {self.from_square}"
            raise ValueError(msg)


@dataclass(frozen=True)
class DropMove:
    """持ち駒を打つ指し手。"""

    square: Square
    kind: PieceKind

    def __post_init__(self) -> None:
        """打てる駒かを確かめる。

        Raises:
            ValueError: 玉を打つ場合。
        """
        if self.kind == PieceKind.KING:
            msg = "玉は打てません。"
            raise ValueError(msg)


# 指し手。盤上の駒を動かす手(NormalMove)か、持ち駒を打つ手(DropMove)のどちらか。
# 移動元と打つ駒を両方持つ、または両方持たない指し手を作れないように、2つのクラスに分けている。
type Move = NormalMove | DropMove
