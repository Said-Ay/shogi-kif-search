# Copyright (C) 2026 Said-Ay
# SPDX-License-Identifier: GPL-3.0-only

"""kif.pyのテスト。"""

import re
from pathlib import Path

import cshogi
import pytest
from cshogi import KIF

from shogi_kif_search.kif import parse_kif_move
from shogi_kif_search.move import DropMove, Move, NormalMove, Square
from shogi_kif_search.piece import PieceKind
from shogi_kif_search.usi import parse_usi

# 棋譜の指し手の行から、手数の後ろの指し手の部分を取り出す。例: `   9 同　銀(68)   ( 0:00/00:00:06)`
_MOVE_LINE_PATTERN = re.compile(r"\s*\d+ (\S+(?:　\S+)?)")

# 指し手の行と同じ形で書かれる終局の言葉
_END_WORDS = frozenset({"投了", "中断", "千日手", "持将棋", "詰み", "切れ負け", "反則勝ち", "反則負け"})


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


def test_parse_kif_game() -> None:
    """棋譜の全指し手が、cshogiの読んだ指し手と一致することを確認する。"""
    kif_text = (Path(__file__).parent / "data" / "game_001.kif").read_text(encoding="utf-8")
    expected_moves = [parse_usi(cshogi.move_to_usi(move)) for move in KIF.Parser.parse_str(kif_text).moves]
    # 指し手の行は「手数 指し手 (消費時間)」の形。投了などの終局の行は指し手ではないので除く
    texts = [
        match.group(1)
        for line in kif_text.splitlines()
        if (match := _MOVE_LINE_PATTERN.match(line)) and match.group(1) not in _END_WORDS
    ]

    moves: list[Move] = []
    previous_to: Square | None = None
    for text in texts:
        move = parse_kif_move(text, previous_to)
        moves.append(move)
        previous_to = move.to_square if isinstance(move, NormalMove) else move.square

    assert len(moves) == len(expected_moves) == 76  # noqa: PLR2004 棋譜の手数
    assert moves == expected_moves


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
