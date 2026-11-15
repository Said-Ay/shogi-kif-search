# Copyright (C) 2026 Said-Ay
# SPDX-License-Identifier: GPL-3.0-only

"""局面を定義する。"""

from typing import TYPE_CHECKING, Self

from shogi_kif_search.move import DropMove, Move, NormalMove, Square
from shogi_kif_search.piece import BOARD_SIZE, HAND_PIECE_KINDS, Color, Piece, PieceKind

if TYPE_CHECKING:
    from collections.abc import Mapping, Sequence


class Position:
    """局面を表すクラス。盤上の駒、持ち駒、手番、手数を持つ。

    盤面は `board[段][筋]` の9行9列で持ち、`board[0][0]` が９一、`board[8][8]` が１九になる。
    空きマスは `None` で表す。
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

        Args:
            board: 9行9列の盤面。行ごとにコピーして保持する。
            hands: 先後ごとの持ち駒の枚数。省略した駒種と先後は0枚で補う。
            turn: 手番。
            move_number: 手数。

        Raises:
            ValueError: 盤面が9行9列でない、持ち駒の枚数が負、または持ち駒に玉がある場合。
        """
        # サイズと玉の確認
        if len(board) != BOARD_SIZE or any(len(row) != BOARD_SIZE for row in board):
            msg = f"盤面のサイズが異なります。board: {board}"
            raise ValueError(msg)
        self.board = [list(row) for row in board]
        for hand in hands.values():
            if PieceKind.KING in hand:
                msg = f"持ち駒に玉があることはありません。hands: {hands}"
                raise ValueError(msg)

        # 持ち駒コピー、０枚の補完及び持ち駒の枚数が負でないかを確認する
        self.hands = {}
        for color in Color:
            self.hands[color] = {}
            for kind in HAND_PIECE_KINDS:
                count = hands.get(color, {}).get(kind, 0)
                if count < 0:
                    msg = f"持ち駒の枚数が負です。color: {color}, kind: {kind}, count: {count}"
                    raise ValueError(msg)
                self.hands[color][kind] = count

        self.turn = turn
        self.move_number = move_number

    @staticmethod
    def square_to_index(square: Square) -> tuple[int, int]:
        """マス目を盤面のインデックスに変換する。

        例えば２二は、2筋2段なので `(1, 7)` になる。
        筋と段の範囲は `Square` が確かめるので、ここでは確かめない。

        Args:
            square: マス目。

        Returns:
            盤面の `(行, 列)` のタプル。行は段から、列は筋から決まる。
        """
        return square.rank - 1, BOARD_SIZE - square.file

    @classmethod
    def initial(cls) -> Self:
        """平手の初期局面を作る。

        Returns:
            先手番、手数1、持ち駒なしの平手の初期局面。
        """
        back_rank = [
            PieceKind.LANCE,
            PieceKind.KNIGHT,
            PieceKind.SILVER,
            PieceKind.GOLD,
            PieceKind.KING,
            PieceKind.GOLD,
            PieceKind.SILVER,
            PieceKind.KNIGHT,
            PieceKind.LANCE,
        ]
        board: Sequence[Sequence[Piece | None]] = [
            [Piece(kind, Color.WHITE) for kind in back_rank],
            [
                None,
                Piece(PieceKind.ROOK, Color.WHITE),
                None,
                None,
                None,
                None,
                None,
                Piece(PieceKind.BISHOP, Color.WHITE),
                None,
            ],
            [Piece(PieceKind.PAWN, Color.WHITE)] * BOARD_SIZE,
            [None] * BOARD_SIZE,
            [None] * BOARD_SIZE,
            [None] * BOARD_SIZE,
            [Piece(PieceKind.PAWN, Color.BLACK)] * BOARD_SIZE,
            [
                None,
                Piece(PieceKind.BISHOP, Color.BLACK),
                None,
                None,
                None,
                None,
                None,
                Piece(PieceKind.ROOK, Color.BLACK),
                None,
            ],
            [Piece(kind, Color.BLACK) for kind in back_rank],
        ]
        return cls(board, hands={}, turn=Color.BLACK, move_number=1)

    def push(self, move: Move) -> None:
        """局面に1手指す。

        局面そのものを書き換え、手番を入れ替えて手数を1増やす。
        将棋のルール違反は確かめない。

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
        self.turn = Color.WHITE if self.turn == Color.BLACK else Color.BLACK
        self.move_number += 1

    def _push_normal(self, move: NormalMove) -> None:
        """盤上の駒を動かす。相手の駒があれば取って、手番側の持ち駒に加える。"""
        from_row, from_col = self.square_to_index(move.from_square)
        to_row, to_col = self.square_to_index(move.to_square)

        piece = self.board[from_row][from_col]
        if piece is None:
            msg = f"移動元に駒がありません。from_square: {move.from_square}"
            raise ValueError(msg)

        if piece.color != self.turn:
            msg = "手番側の駒ではありません。"
            raise ValueError(msg)

        captured = self.board[to_row][to_col]
        if captured is not None:
            if captured.kind == PieceKind.KING:
                msg = "玉は取れません。"
                raise ValueError(msg)
            if captured.color == self.turn:
                msg = "自分の駒は取れません。"
                raise ValueError(msg)

        if move.promote:
            if piece.promoted:
                msg = "すでに成っている駒は成れません。"
                raise ValueError(msg)
            piece = Piece(piece.kind, piece.color, promoted=True)
        if captured is not None:
            # 成り駒を取っても、持ち駒には成っていない種類で入る
            self.hands[self.turn][captured.kind] += 1
        self.board[to_row][to_col] = piece
        self.board[from_row][from_col] = None

    def _push_drop(self, move: DropMove) -> None:
        """持ち駒を打つ。"""
        row, col = self.square_to_index(move.square)
        if self.hands[self.turn][move.kind] <= 0:
            msg = "持ち駒がありません。"
            raise ValueError(msg)
        if self.board[row][col] is not None:
            msg = "駒があるマスには打てません。"
            raise ValueError(msg)

        self.board[row][col] = Piece(move.kind, self.turn)
        self.hands[self.turn][move.kind] -= 1
