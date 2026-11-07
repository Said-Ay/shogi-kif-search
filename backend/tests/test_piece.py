# Copyright (C) 2026 Said-Ay
# SPDX-License-Identifier: GPL-3.0-only

"""piece.pyのテスト。"""

import pytest

from shogi_kif_search.piece import Color, Piece, PieceKind


def test_promote_gold_and_king() -> None:
    """金と玉は成ることができないことを確認する。"""
    with pytest.raises(ValueError, match="金と玉は成ることができません。"):
        Piece(kind=PieceKind.GOLD, color=Color.BLACK, promoted=True)

    with pytest.raises(ValueError, match="金と玉は成ることができません。"):
        Piece(kind=PieceKind.KING, color=Color.BLACK, promoted=True)


def test_promote_other_pieces() -> None:
    """金と玉以外の駒は成ることができることを確認する。"""
    for kind in [
        PieceKind.PAWN,
        PieceKind.LANCE,
        PieceKind.KNIGHT,
        PieceKind.SILVER,
        PieceKind.BISHOP,
        PieceKind.ROOK,
    ]:
        piece = Piece(kind=kind, color=Color.BLACK, promoted=True)
        assert piece.promoted is True


def test_piece_in_dict() -> None:
    """駒を辞書のキーとして使用できることを確認する。"""
    piece1 = Piece(kind=PieceKind.PAWN, color=Color.BLACK, promoted=False)
    piece2 = Piece(kind=PieceKind.PAWN, color=Color.BLACK, promoted=False)
    piece3 = Piece(kind=PieceKind.PAWN, color=Color.WHITE, promoted=False)

    piece_dict = {piece1: "black pawn", piece3: "white pawn"}

    assert piece_dict[piece2] == "black pawn"
    assert piece_dict[piece3] == "white pawn"


def test_piece_equality() -> None:
    """駒の等価性を確認する。"""
    piece1 = Piece(kind=PieceKind.PAWN, color=Color.BLACK, promoted=False)
    piece2 = Piece(kind=PieceKind.PAWN, color=Color.BLACK, promoted=False)
    piece3 = Piece(kind=PieceKind.PAWN, color=Color.WHITE, promoted=False)
    piece4 = Piece(kind=PieceKind.PAWN, color=Color.BLACK, promoted=True)

    assert piece1 == piece2
    assert piece1 != piece3
    assert piece1 != piece4
