# Copyright (C) 2026 Said-Ay
# SPDX-License-Identifier: GPL-3.0-only

"""position.pyのテスト。"""

from pathlib import Path

import cshogi
import pytest
from cshogi import KIF
from hypothesis import given, settings
from hypothesis import strategies as st

from shogi_kif_search.move import DropMove, Move, NormalMove, Square
from shogi_kif_search.piece import HAND_PIECE_KINDS, Color, Piece, PieceKind
from shogi_kif_search.position import Position
from shogi_kif_search.sfen import to_sfen
from shogi_kif_search.usi import parse_usi


def test_invalid_board() -> None:
    """盤面が9行9列でない場合にValueErrorが発生することを確認する。"""
    invalid_board = [[None] * 9] * 8
    with pytest.raises(ValueError, match="盤面のサイズが異なります。"):
        Position(board=invalid_board, hands={}, turn=Color.BLACK, move_number=1)


def test_hands_complementation() -> None:
    """持ち駒の不足分が0で補完されることを確認する。"""
    hands = {Color.BLACK: {PieceKind.ROOK: 1}}

    position = Position(
        board=[[None] * 9 for _ in range(9)],
        hands=hands,
        turn=Color.BLACK,
        move_number=1,
    )

    expected_black = {
        PieceKind.ROOK: 1,
        PieceKind.BISHOP: 0,
        PieceKind.GOLD: 0,
        PieceKind.SILVER: 0,
        PieceKind.KNIGHT: 0,
        PieceKind.LANCE: 0,
        PieceKind.PAWN: 0,
    }
    expected_white = {
        PieceKind.ROOK: 0,
        PieceKind.BISHOP: 0,
        PieceKind.GOLD: 0,
        PieceKind.SILVER: 0,
        PieceKind.KNIGHT: 0,
        PieceKind.LANCE: 0,
        PieceKind.PAWN: 0,
    }
    assert position.hands == {
        Color.BLACK: expected_black,
        Color.WHITE: expected_white,
    }


def test_negative_hand_count() -> None:
    """持ち駒の枚数が負の場合にValueErrorが発生することを確認する。"""
    hands = {Color.BLACK: {PieceKind.ROOK: -1}}
    with pytest.raises(ValueError, match="持ち駒の枚数が負です。"):
        Position(
            board=[[None] * 9 for _ in range(9)],
            hands=hands,
            turn=Color.BLACK,
            move_number=1,
        )


def test_king_in_hands() -> None:
    """持ち駒に玉がある場合にValueErrorが発生することを確認する。"""
    hands = {Color.BLACK: {PieceKind.KING: 1}}
    with pytest.raises(ValueError, match="持ち駒に玉があることはありません。"):
        Position(
            board=[[None] * 9 for _ in range(9)],
            hands=hands,
            turn=Color.BLACK,
            move_number=1,
        )


def test_hands_copy() -> None:
    """元の持ち駒を変更しても局面が変化しないことを確認する。"""
    pawn_count = 2
    original_hands = {Color.BLACK: {PieceKind.PAWN: pawn_count}}

    position = Position(
        board=[[None] * 9 for _ in range(9)],
        hands=original_hands,
        turn=Color.BLACK,
        move_number=1,
    )

    # Position を生成した後、元の辞書を書き換える
    original_hands[Color.BLACK][PieceKind.PAWN] = 5

    # Position 内部の値は変わっていないはず
    assert position.hands[Color.BLACK][PieceKind.PAWN] == pawn_count


def test_board_copy() -> None:
    """元の盤面を変更しても局面の盤面が変わらないことを確認する。"""
    original_board: list[list[Piece | None]] = [[None] * 9 for _ in range(9)]

    position = Position(
        board=original_board,
        hands={},
        turn=Color.BLACK,
        move_number=1,
    )

    # Position の生成後に、元の盤面を変更する
    original_board[0][0] = Piece(
        kind=PieceKind.ROOK,
        color=Color.WHITE,
    )

    # Position 内部の盤面は変更されない
    assert position.board[0][0] is None


@pytest.mark.parametrize(
    ("file_num", "rank_num", "expected"),
    [
        (2, 2, (1, 7)),
        (8, 2, (1, 1)),
        (2, 8, (7, 7)),
        (9, 1, (0, 0)),
        (1, 1, (0, 8)),
        (9, 9, (8, 0)),
        (1, 9, (8, 8)),
        (5, 5, (4, 4)),
    ],
)
def test_square_to_index(file_num: int, rank_num: int, expected: tuple[int, int]) -> None:
    """square_to_index()がマス目を盤面のインデックスに変換することを確認する。"""
    assert Position.square_to_index(Square(file_num, rank_num)) == expected


def test_initial() -> None:
    """initial()で初期局面が正しく生成されることを確認する。"""
    position = Position.initial()

    b = Color.BLACK
    w = Color.WHITE
    k = PieceKind

    expected_board = [
        [
            Piece(kind, w)
            for kind in (
                k.LANCE,
                k.KNIGHT,
                k.SILVER,
                k.GOLD,
                k.KING,
                k.GOLD,
                k.SILVER,
                k.KNIGHT,
                k.LANCE,
            )
        ],
        [None, Piece(k.ROOK, w), None, None, None, None, None, Piece(k.BISHOP, w), None],
        [Piece(k.PAWN, w)] * 9,
        [None] * 9,
        [None] * 9,
        [None] * 9,
        [Piece(k.PAWN, b)] * 9,
        [None, Piece(k.BISHOP, b), None, None, None, None, None, Piece(k.ROOK, b), None],
        [
            Piece(kind, b)
            for kind in (
                k.LANCE,
                k.KNIGHT,
                k.SILVER,
                k.GOLD,
                k.KING,
                k.GOLD,
                k.SILVER,
                k.KNIGHT,
                k.LANCE,
            )
        ],
    ]

    assert position.board == expected_board
    assert position.turn == Color.BLACK
    assert position.hands == {
        Color.BLACK: dict.fromkeys(HAND_PIECE_KINDS, 0),
        Color.WHITE: dict.fromkeys(HAND_PIECE_KINDS, 0),
    }
    assert position.move_number == 1


def _piece_at(position: Position, square: Square) -> Piece | None:
    """局面の、指定したマス目にある駒を返す。"""
    row, col = Position.square_to_index(square)
    return position.board[row][col]


def _position_with(pieces: dict[Square, Piece], hands: dict[Color, dict[PieceKind, int]]) -> Position:
    """両方の玉と、指定した駒だけを置いた先手番・手数1の局面を作る。

    先手の玉は５九、後手の玉は５一に置く。
    """
    board: list[list[Piece | None]] = [[None] * 9 for _ in range(9)]
    all_pieces = {
        Square(5, 9): Piece(PieceKind.KING, Color.BLACK),
        Square(5, 1): Piece(PieceKind.KING, Color.WHITE),
        **pieces,
    }
    for square, piece in all_pieces.items():
        row, col = Position.square_to_index(square)
        board[row][col] = piece
    return Position(board=board, hands=hands, turn=Color.BLACK, move_number=1)


def test_push_move() -> None:
    """駒を動かすと、移動元が空き、移動先に駒が置かれ、手番と手数が進むことを確認する。"""
    position = Position.initial()

    position.push(NormalMove(from_square=Square(2, 7), to_square=Square(2, 6), promote=False))

    assert _piece_at(position, Square(2, 7)) is None
    assert _piece_at(position, Square(2, 6)) == Piece(PieceKind.PAWN, Color.BLACK)
    assert position.turn == Color.WHITE
    assert position.move_number == 2  # noqa: PLR2004 平手の手数1から1手進めた値


def test_push_capture() -> None:
    """相手の駒を取ると、取った駒が手番側の持ち駒に1枚増えることを確認する。"""
    position = _position_with(
        pieces={
            Square(2, 5): Piece(PieceKind.PAWN, Color.BLACK),
            Square(2, 4): Piece(PieceKind.PAWN, Color.WHITE),
        },
        hands={},
    )

    position.push(NormalMove(from_square=Square(2, 5), to_square=Square(2, 4), promote=False))

    assert _piece_at(position, Square(2, 5)) is None
    assert _piece_at(position, Square(2, 4)) == Piece(PieceKind.PAWN, Color.BLACK)
    assert position.hands[Color.BLACK][PieceKind.PAWN] == 1
    assert position.hands[Color.WHITE][PieceKind.PAWN] == 0


def test_push_promote() -> None:
    """成る手では、移動先の駒が成った駒になることを確認する。"""
    position = _position_with(
        pieces={Square(2, 4): Piece(PieceKind.PAWN, Color.BLACK)},
        hands={},
    )

    position.push(NormalMove(from_square=Square(2, 4), to_square=Square(2, 3), promote=True))

    assert _piece_at(position, Square(2, 4)) is None
    assert _piece_at(position, Square(2, 3)) == Piece(PieceKind.PAWN, Color.BLACK, promoted=True)


def test_push_capture_promoted() -> None:
    """成り駒を取ると、成っていない種類として持ち駒に入ることを確認する。

    先手の銀で後手の龍を取り、先手の持ち駒に飛が1枚増えることを確かめる。
    """
    position = _position_with(
        pieces={
            Square(2, 4): Piece(PieceKind.SILVER, Color.BLACK),
            Square(2, 3): Piece(PieceKind.ROOK, Color.WHITE, promoted=True),
        },
        hands={},
    )

    position.push(NormalMove(from_square=Square(2, 4), to_square=Square(2, 3), promote=False))

    assert _piece_at(position, Square(2, 3)) == Piece(PieceKind.SILVER, Color.BLACK)
    assert position.hands[Color.BLACK][PieceKind.ROOK] == 1


def test_push_drop() -> None:
    """駒を打つと、成っていない駒が置かれ、持ち駒が1枚減ることを確認する。"""
    position = _position_with(pieces={}, hands={Color.BLACK: {PieceKind.ROOK: 1}})

    position.push(DropMove(square=Square(5, 5), kind=PieceKind.ROOK))

    assert _piece_at(position, Square(5, 5)) == Piece(PieceKind.ROOK, Color.BLACK)
    assert position.hands[Color.BLACK][PieceKind.ROOK] == 0
    assert position.turn == Color.WHITE
    assert position.move_number == 2  # noqa: PLR2004 手数1から1手進めた値


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
            {Square(2, 4): Piece(PieceKind.PAWN, Color.BLACK, promoted=True)},
            {},
            NormalMove(from_square=Square(2, 4), to_square=Square(2, 3), promote=True),
            "成っている駒は成れません。",
            id="promote_promoted_piece",
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


def test_push_kif_game() -> None:
    """KIFの全指し手について、適用後のSFENがcshogiと一致することを確認する。"""
    kif_path = Path(__file__).parent / "data" / "game_001.kif"
    kif_text = kif_path.read_text(encoding="utf-8")
    kif = KIF.Parser.parse_str(kif_text)
    expected_length = 76

    board = cshogi.Board()
    position = Position.initial()

    assert len(kif.moves) == expected_length, f"指し手の数が{expected_length}ではありません。"
    assert to_sfen(position) == board.sfen()

    for move_number, move in enumerate(kif.moves, start=1):
        usi = cshogi.move_to_usi(move)

        board.push(move)
        position.push(parse_usi(usi))

        assert to_sfen(position) == board.sfen(), f"{move_number}手目({usi})でSFENが一致しません"


@settings(max_examples=30, deadline=None)
@given(st.data())
def test_push_random(data: st.DataObject) -> None:
    """ランダムな合法手を指して、適用後のSFENがcshogiと一致することを確認する。"""
    board = cshogi.Board()
    position = Position.initial()
    for move_number in range(1, 71):  # 70手まで
        legal_moves = list(board.legal_moves)
        if not legal_moves:
            break  # 詰み
        move = data.draw(st.sampled_from(legal_moves))
        usi = cshogi.move_to_usi(move)
        board.push(move)
        position.push(parse_usi(usi))

        assert to_sfen(position) == board.sfen(), f"{move_number}手目({usi})でSFENが一致しません"
