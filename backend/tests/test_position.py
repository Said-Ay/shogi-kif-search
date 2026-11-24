# Copyright (C) 2026 Said-Ay
# SPDX-License-Identifier: GPL-3.0-only

"""position.pyのテスト。"""

import cshogi
import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

from shogi_kif_search.move import DropMove, Move, NormalMove, Square
from shogi_kif_search.piece import BOARD_SIZE, Color, Piece, PieceKind
from shogi_kif_search.position import Position
from shogi_kif_search.sfen import to_sfen
from shogi_kif_search.usi import parse_usi

# ランダムな対局で指す手数の上限
MAX_RANDOM_MOVES = 70


def _empty_board() -> list[list[Piece | None]]:
    """駒のない9行9列の盤面を作る。"""
    return [[None] * BOARD_SIZE for _ in range(BOARD_SIZE)]


def _position_with(pieces: dict[Square, Piece], hands: dict[Color, dict[PieceKind, int]]) -> Position:
    """両方の玉と、指定した駒だけを置いた先手番・手数1の局面を作る。

    先手の玉は５九、後手の玉は５一に置く。
    """
    board = _empty_board()
    all_pieces = {
        Square(5, 9): Piece(PieceKind.KING, Color.BLACK),
        Square(5, 1): Piece(PieceKind.KING, Color.WHITE),
        **pieces,
    }
    for square, piece in all_pieces.items():
        row, col = Position.square_to_index(square)
        board[row][col] = piece
    return Position(board=board, hands=hands, turn=Color.BLACK, move_number=1)


@pytest.mark.parametrize(
    ("board", "hands", "message"),
    [
        pytest.param([[None] * 9] * 8, {}, "盤面は9行9列です。", id="8_rows"),
        pytest.param(
            _empty_board(), {Color.BLACK: {PieceKind.KING: 1}}, "玉は持ち駒になりません。", id="king"
        ),
        pytest.param(
            _empty_board(), {Color.BLACK: {PieceKind.ROOK: -1}}, "持ち駒の枚数が負です。", id="negative"
        ),
    ],
)
def test_constructor_invalid(
    board: list[list[Piece | None]], hands: dict[Color, dict[PieceKind, int]], message: str
) -> None:
    """盤面の大きさや持ち駒がおかしい局面はValueErrorになることを確認する。"""
    with pytest.raises(ValueError, match=message):
        Position(board=board, hands=hands, turn=Color.BLACK, move_number=1)


def test_constructor_copies_and_fills_hands() -> None:
    """盤面と持ち駒をコピーして持ち、省略した持ち駒を0枚にすることを確認する。"""
    board = _empty_board()
    hands = {Color.BLACK: {PieceKind.PAWN: 2}}
    position = Position(board=board, hands=hands, turn=Color.BLACK, move_number=1)

    # 作った後に呼び出し元の盤面と持ち駒を変えても、局面は変わらない
    board[0][0] = Piece(PieceKind.ROOK, Color.WHITE)
    hands[Color.BLACK][PieceKind.PAWN] = 5

    assert position.board[0][0] is None
    assert position.hands[Color.BLACK][PieceKind.PAWN] == 2  # noqa: PLR2004 作ったときに渡した枚数
    assert position.hands[Color.WHITE][PieceKind.ROOK] == 0


@pytest.mark.parametrize(
    ("square", "expected"),
    [(Square(9, 1), (0, 0)), (Square(2, 2), (1, 7)), (Square(1, 9), (8, 8))],
)
def test_square_to_index(square: Square, expected: tuple[int, int]) -> None:
    """マス目が盤面の行と列に変換され、行と列からマス目に戻せることを確認する。"""
    assert Position.square_to_index(square) == expected
    assert Position.index_to_square(*expected) == square


# 局面として起こりえない手。どれも先手番で指す
@pytest.mark.parametrize(
    ("pieces", "hands", "move", "message"),
    [
        pytest.param(
            {},
            {},
            NormalMove(from_square=Square(2, 5), to_square=Square(2, 4), promote=False),
            "移動元に駒がありません。",
            id="empty_from_square",
        ),
        pytest.param(
            {Square(2, 4): Piece(PieceKind.PAWN, Color.WHITE)},
            {},
            NormalMove(from_square=Square(2, 4), to_square=Square(2, 5), promote=False),
            "手番側の駒ではありません。",
            id="move_opponent_piece",
        ),
        pytest.param(
            {
                Square(2, 5): Piece(PieceKind.PAWN, Color.BLACK),
                Square(2, 4): Piece(PieceKind.SILVER, Color.BLACK),
            },
            {},
            NormalMove(from_square=Square(2, 5), to_square=Square(2, 4), promote=False),
            "自分の駒は取れません。",
            id="capture_own_piece",
        ),
        pytest.param(
            {Square(5, 3): Piece(PieceKind.ROOK, Color.BLACK)},
            {},
            NormalMove(from_square=Square(5, 3), to_square=Square(5, 1), promote=False),
            "玉は取れません。",
            id="capture_king",
        ),
        pytest.param(
            {
                Square(2, 4): Piece(PieceKind.PAWN, Color.BLACK, promoted=True),
                Square(2, 3): Piece(PieceKind.PAWN, Color.WHITE),
            },
            {},
            NormalMove(from_square=Square(2, 4), to_square=Square(2, 3), promote=True),
            "成っている駒は成れません。",
            id="capture_and_promote_promoted_piece",
        ),
        pytest.param(
            {},
            {},
            DropMove(square=Square(5, 5), kind=PieceKind.PAWN),
            "持ち駒がありません。",
            id="drop_without_hand",
        ),
        pytest.param(
            {Square(5, 5): Piece(PieceKind.PAWN, Color.WHITE)},
            {Color.BLACK: {PieceKind.PAWN: 1}},
            DropMove(square=Square(5, 5), kind=PieceKind.PAWN),
            "駒があるマスには打てません。",
            id="drop_on_occupied_square",
        ),
    ],
)
def test_push_invalid(
    pieces: dict[Square, Piece],
    hands: dict[Color, dict[PieceKind, int]],
    move: Move,
    message: str,
) -> None:
    """局面として起こりえない手はValueErrorになり、局面が変わらないことを確認する。"""
    position = _position_with(pieces=pieces, hands=hands)
    before = to_sfen(position)

    with pytest.raises(ValueError, match=message):
        position.push(move)

    # 盤面・手番・持ち駒・手数のどれも書き換わっていない
    assert to_sfen(position) == before


@settings(max_examples=30, deadline=None)
@given(st.data())
def test_push_random(data: st.DataObject) -> None:
    """cshogiの合法手をランダムに指して、毎手の局面がcshogiと一致することを確認する。"""
    board = cshogi.Board()
    position = Position.initial()
    for move_number in range(1, MAX_RANDOM_MOVES + 1):
        legal_moves = list(board.legal_moves)
        if not legal_moves:
            break  # 詰み
        move = data.draw(st.sampled_from(legal_moves))
        usi = cshogi.move_to_usi(move)
        board.push(move)
        position.push(parse_usi(usi))
        assert to_sfen(position) == board.sfen(), f"{move_number}手目({usi})でSFENが一致しません"
