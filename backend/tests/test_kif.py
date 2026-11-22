# Copyright (C) 2026 Said-Ay
# SPDX-License-Identifier: GPL-3.0-only

"""kif.pyのテスト。"""

from typing import TYPE_CHECKING

import cshogi
import pytest
from cshogi import KIF

from shogi_kif_search.kif import KifGame, parse_kif, parse_kif_move, read_kif
from shogi_kif_search.move import DropMove, Move, NormalMove, Square
from shogi_kif_search.piece import PieceKind
from shogi_kif_search.usi import parse_usi

if TYPE_CHECKING:
    from pathlib import Path

# parse_kif のテストで使う初手から3手の指し手
_FIRST_MOVES = (
    NormalMove(Square(2, 7), Square(2, 6), promote=False),
    NormalMove(Square(8, 3), Square(8, 4), promote=False),
    NormalMove(Square(2, 6), Square(2, 5), promote=False),
)


@pytest.mark.parametrize(
    ("text", "expected"),
    [
        ("７六歩(77)", NormalMove(Square(7, 7), Square(7, 6), promote=False)),
        ("２二角成(88)", NormalMove(Square(8, 8), Square(2, 2), promote=True)),
        ("５五角打", DropMove(Square(5, 5), PieceKind.BISHOP)),
    ],
)
def test_parse_kif_move(text: str, expected: Move) -> None:
    """KIF形式の指し手が、対応する指し手の型に変換されることを確認する。"""
    assert parse_kif_move(text) == expected


@pytest.mark.parametrize(
    ("text", "promote"),
    [("２二銀成(31)", True), ("２二成銀(31)", False), ("９二馬(91)", False)],
)
def test_parse_kif_move_promote(text: str, *, promote: bool) -> None:
    """駒の名前の後ろの「成」だけを成る手とし、成銀などの駒の名前とは区別することを確認する。"""
    move = parse_kif_move(text)
    assert isinstance(move, NormalMove)
    assert move.promote is promote


def test_parse_kif_move_alias() -> None:
    """同じ駒の別の書き方が、同じ指し手に変換されることを確認する。"""
    assert parse_kif_move("２二成銀(31)") == parse_kif_move("２二全(31)")


@pytest.mark.parametrize("text", ["同　歩(23)", "同歩(23)"])
def test_parse_kif_move_same(text: str) -> None:
    """「同」が、全角空白の有無にかかわらず直前の指し手の移動先に変換されることを確認する。"""
    expected = NormalMove(Square(2, 3), Square(2, 4), promote=False)
    assert parse_kif_move(text, previous_to=Square(2, 4)) == expected


def test_read_kif_game(game_001_path: Path) -> None:
    """棋譜ファイルの全指し手が、cshogiの読んだ指し手と一致することを確認する。

    ヘッダーの未知の行は読み捨て、投了の行とその後ろの行は指し手にならない。
    """
    kif_text = game_001_path.read_text(encoding="utf-8")
    expected_moves = tuple(
        parse_usi(cshogi.move_to_usi(move)) for move in KIF.Parser.parse_str(kif_text).moves
    )

    game = read_kif(game_001_path)

    assert len(game.moves) == 76  # noqa: PLR2004 棋譜の手数
    assert game == KifGame(handicap="平手", moves=expected_moves)


@pytest.mark.parametrize("encoding", ["utf-8-sig", "cp932"])
def test_read_kif_encoding(tmp_path: Path, game_001_path: Path, encoding: str) -> None:
    """BOM付きのUTF-8とcp932の棋譜ファイルも、UTF-8と同じ内容に読めることを確認する。"""
    path = tmp_path / "game.kif"
    path.write_bytes(game_001_path.read_text(encoding="utf-8").encode(encoding))
    assert read_kif(path) == read_kif(game_001_path)


@pytest.mark.parametrize(
    "text",
    [
        pytest.param(
            "手合割：平手\n手数----指手--\n1 ２六歩(27)\n2 ８四歩(83)\n3 ２五歩(26)\n4 中断\n5 ７六歩(77)\n",
            id="end_line",
        ),
        pytest.param(
            "1 ２六歩(27)\n2 ８四歩(83)\n3 ２五歩(26)+\n\n変化：3手\n3 ７六歩(77)\n",
            id="variation_without_end_line",
        ),
        pytest.param(
            "# コメント\n先手段級：初段\n1 ２六歩(27)\n*指し手のコメント\n2 ８四歩(83)\n3 ２五歩(26)\n",
            id="comment_and_unknown_header",
        ),
    ],
)
def test_parse_kif(text: str) -> None:
    """終局の行か変化の行で止まり、コメントと未知のヘッダーを読み捨てることを確認する。

    手合割を省略した棋譜は平手として読む。
    """
    assert parse_kif(text) == KifGame(handicap="平手", moves=_FIRST_MOVES)


@pytest.mark.parametrize(
    ("text", "message"),
    [
        ("1 ２六歩(27)\n3 ８四歩(83)\n", "2行目: 手数が2ではありません。"),
        ("手合割：香落ち\n", "1行目: 平手以外の手合割には対応していません。"),
        ("1 ２六歩(27)\n&しおり\n", "2行目: しおりには対応していません。"),
        ("1 ２六歩(27)\nまで1手\n", "2行目: KIF形式の行として読めません。"),
        ("1 同　歩(23)\n", "1行目: 直前の指し手がないので「同」を解釈できません。"),
    ],
)
def test_parse_kif_invalid(text: str, message: str) -> None:
    """手数の欠け、平手以外の手合割、しおり、どの形式にも当てはまらない行、読めない指し手はValueErrorになることを確認する。"""
    with pytest.raises(ValueError, match=message):
        parse_kif(text)


@pytest.mark.parametrize(
    ("text", "message"),
    [
        ("２二銀不成(31)", "KIFの仕様に「不成」はありません。"),
        ("７六歩", "KIF形式の指し手として読めません。"),
        ("同　歩(23)", "直前の指し手がないので「同」を解釈できません。"),
    ],
)
def test_parse_kif_move_invalid(text: str, message: str) -> None:
    """不成と、KIF形式の指し手として読めない文字列はValueErrorになることを確認する。"""
    with pytest.raises(ValueError, match=message):
        parse_kif_move(text)
