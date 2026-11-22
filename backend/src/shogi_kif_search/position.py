# Copyright (C) 2026 Said-Ay
# SPDX-License-Identifier: GPL-3.0-only

"""局面を定義する。"""

from typing import TYPE_CHECKING, Self

from shogi_kif_search.move import DropMove, Move, NormalMove, Square
from shogi_kif_search.piece import BOARD_SIZE, HAND_PIECE_KINDS, Color, Piece, PieceKind

if TYPE_CHECKING:
    from collections.abc import Mapping, Sequence

# 平手で一段目と九段目に並ぶ駒。９筋から１筋の順
_BACK_RANK = (
    PieceKind.LANCE,
    PieceKind.KNIGHT,
    PieceKind.SILVER,
    PieceKind.GOLD,
    PieceKind.KING,
    PieceKind.GOLD,
    PieceKind.SILVER,
    PieceKind.KNIGHT,
    PieceKind.LANCE,
)


class Position:
    """局面。盤上の駒、持ち駒、手番、手数を持つ。

    盤面は `board[段][筋]` の9行9列で持ち、`board[0][0]` が９一、`board[8][8]` が１九になる。
    空きマスは `None` で表す。持ち駒は先後ごとに、持ち駒になる7種類すべての枚数を持つ。
    """

    board: list[list[Piece | None]]
    hands: dict[Color, dict[PieceKind, int]]
    turn: Color
    move_number: int

    def __init__(
        self,
        board: Sequence[Sequence[Piece | None]],
        hands: Mapping[Color, Mapping[PieceKind, int]],
        turn: Color,
        move_number: int,
    ) -> None:
        """局面を作る。

        受け取った盤面と持ち駒はコピーして持つので、後から呼び出し元で変えても局面は変わらない。

        Args:
            board: 9行9列の盤面。
            hands: 先後ごとの持ち駒の枚数。省略した先後と駒の種類は0枚とする。
            turn: 手番。
            move_number: 手数。

        Raises:
            ValueError: 盤面が9行9列でない、持ち駒に玉がある、または持ち駒の枚数が負の場合。
        """
        if len(board) != BOARD_SIZE or any(len(row) != BOARD_SIZE for row in board):
            msg = f"盤面は{BOARD_SIZE}行{BOARD_SIZE}列です。"
            raise ValueError(msg)
        for color, hand in hands.items():
            if PieceKind.KING in hand:
                msg = f"玉は持ち駒になりません。color: {color}"
                raise ValueError(msg)
            for kind, count in hand.items():
                if count < 0:
                    msg = f"持ち駒の枚数が負です。color: {color}, kind: {kind}, count: {count}"
                    raise ValueError(msg)

        self.board = [list(row) for row in board]
        self.hands = {
            color: {kind: hands.get(color, {}).get(kind, 0) for kind in HAND_PIECE_KINDS} for color in Color
        }
        self.turn = turn
        self.move_number = move_number

    @classmethod
    def initial(cls) -> Self:
        """平手の初期局面を作る。

        Returns:
            先手番、手数1、持ち駒なしの平手の初期局面。
        """
        board: list[list[Piece | None]] = [[None] * BOARD_SIZE for _ in range(BOARD_SIZE)]
        board[0] = [Piece(kind, Color.WHITE) for kind in _BACK_RANK]
        board[2] = [Piece(PieceKind.PAWN, Color.WHITE)] * BOARD_SIZE
        board[6] = [Piece(PieceKind.PAWN, Color.BLACK)] * BOARD_SIZE
        board[8] = [Piece(kind, Color.BLACK) for kind in _BACK_RANK]
        for square, piece in (
            (Square(8, 2), Piece(PieceKind.ROOK, Color.WHITE)),
            (Square(2, 2), Piece(PieceKind.BISHOP, Color.WHITE)),
            (Square(8, 8), Piece(PieceKind.BISHOP, Color.BLACK)),
            (Square(2, 8), Piece(PieceKind.ROOK, Color.BLACK)),
        ):
            row, col = cls.square_to_index(square)
            board[row][col] = piece
        return cls(board, hands={}, turn=Color.BLACK, move_number=1)

    @staticmethod
    def square_to_index(square: Square) -> tuple[int, int]:
        """マス目を盤面の `(行, 列)` に変換する。

        行は段から、列は筋から決まる。例えば２二は `(1, 7)` になる。

        Args:
            square: マス目。

        Returns:
            盤面の `(行, 列)`。
        """
        return square.rank - 1, BOARD_SIZE - square.file

    @staticmethod
    def index_to_square(row: int, col: int) -> Square:
        """盤面の `(行, 列)` をマス目に変換する。`square_to_index` の逆。

        Args:
            row: 盤面の行。0 が一段目。
            col: 盤面の列。0 が9筋。

        Returns:
            マス目。
        """
        return Square(file=BOARD_SIZE - col, rank=row + 1)

    def push(self, move: Move) -> None:
        """局面に1手指す。

        局面そのものを書き換え、手番を入れ替えて手数を1増やす。
        将棋のルール違反は確かめず、局面として起こりえない手だけを、書き換える前に確かめる。

        Args:
            move: 指す手。

        Raises:
            ValueError: 局面として起こりえない手の場合。移動元が空きマス、相手の駒を動かす、
                自分の駒や玉を取る、成り駒をさらに成る、持っていない駒を打つ、駒のあるマスに打つ。
        """
        if isinstance(move, NormalMove):
            self._push_normal(move)
        else:
            self._push_drop(move)
        self.turn = self.turn.opponent
        self.move_number += 1

    def _push_normal(self, move: NormalMove) -> None:
        """盤上の駒を動かす。相手の駒があれば取って、手番側の持ち駒に加える。"""
        from_row, from_col = self.square_to_index(move.from_square)
        to_row, to_col = self.square_to_index(move.to_square)
        piece = self.board[from_row][from_col]
        captured = self.board[to_row][to_col]

        # 書き換える前に、局面として起こりえない手かを確かめる
        if piece is None:
            msg = f"移動元に駒がありません。from_square: {move.from_square}"
            raise ValueError(msg)
        if piece.color != self.turn:
            msg = f"手番側の駒ではありません。from_square: {move.from_square}"
            raise ValueError(msg)
        if captured is not None and captured.kind == PieceKind.KING:
            msg = f"玉は取れません。to_square: {move.to_square}"
            raise ValueError(msg)
        if captured is not None and captured.color == self.turn:
            msg = f"自分の駒は取れません。to_square: {move.to_square}"
            raise ValueError(msg)
        if move.promote and piece.promoted:
            msg = f"成っている駒は成れません。from_square: {move.from_square}"
            raise ValueError(msg)

        if captured is not None:
            # 成り駒を取っても、持ち駒には成っていない種類で入る
            self.hands[self.turn][captured.kind] += 1
        self.board[to_row][to_col] = Piece(piece.kind, piece.color, promoted=True) if move.promote else piece
        self.board[from_row][from_col] = None

    def _push_drop(self, move: DropMove) -> None:
        """持ち駒を打つ。"""
        row, col = self.square_to_index(move.square)

        # 書き換える前に、局面として起こりえない手かを確かめる
        if self.hands[self.turn][move.kind] == 0:
            msg = f"持ち駒がありません。kind: {move.kind}"
            raise ValueError(msg)
        if self.board[row][col] is not None:
            msg = f"駒があるマスには打てません。square: {move.square}"
            raise ValueError(msg)

        self.board[row][col] = Piece(move.kind, self.turn)
        self.hands[self.turn][move.kind] -= 1
