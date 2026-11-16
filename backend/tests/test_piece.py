# Copyright (C) 2026 Said-Ay
# SPDX-License-Identifier: GPL-3.0-only

"""piece.pyのテスト。"""

import pytest

from shogi_kif_search.piece import Color, Piece, PieceKind


@pytest.mark.parametrize("kind", [PieceKind.GOLD, PieceKind.KING])
def test_unpromotable_piece(kind: PieceKind) -> None:
    """金と玉は成れないことを確認する。"""
    with pytest.raises(ValueError, match="金と玉は成れません。"):
        Piece(kind, Color.BLACK, promoted=True)


def test_piece_is_hashable() -> None:
    """同じ内容の駒は等しく、辞書のキーに使えることを確認する。"""
    pieces = {Piece(PieceKind.PAWN, Color.BLACK): "black pawn"}
    assert pieces[Piece(PieceKind.PAWN, Color.BLACK)] == "black pawn"
    assert Piece(PieceKind.PAWN, Color.BLACK) != Piece(PieceKind.PAWN, Color.WHITE)


def test_color_opponent() -> None:
    """相手側が先手と後手で入れ替わることを確認する。"""
    assert Color.BLACK.opponent is Color.WHITE
    assert Color.WHITE.opponent is Color.BLACK
