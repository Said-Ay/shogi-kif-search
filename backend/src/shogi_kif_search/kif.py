# Copyright (C) 2026 Said-Ay
# SPDX-License-Identifier: GPL-3.0-only

"""KIF形式の棋譜を読み、手合割と指し手の列を取り出す。"""

import re
from dataclasses import dataclass
from typing import TYPE_CHECKING

from shogi_kif_search.move import DropMove, Move, NormalMove, Square
from shogi_kif_search.piece import PieceKind

if TYPE_CHECKING:
    from collections.abc import Iterator
    from pathlib import Path

# 移動先の筋は全角数字、段は漢数字で書く
_FILES = "１２３４５６７８９"
_RANKS = "一二三四五六七八九"

# 盤上の駒の名前。成銀・成桂・成香も1つの駒の名前として読み、
# その後ろの「成」とは区別する。玉と王、龍と竜、成銀と全、成桂と圭、成香と杏は同じ駒
_BOARD_PIECE_NAMES = "成銀|成桂|成香|歩|香|桂|銀|金|角|飛|玉|王|と|全|圭|杏|馬|龍|竜"

# 持ち駒として打てる駒の名前と、その種類
_DROP_PIECE_KINDS = {
    "歩": PieceKind.PAWN,
    "香": PieceKind.LANCE,
    "桂": PieceKind.KNIGHT,
    "銀": PieceKind.SILVER,
    "金": PieceKind.GOLD,
    "角": PieceKind.BISHOP,
    "飛": PieceKind.ROOK,
}

# 盤上の駒を動かす手。例: ７六歩(77)、２二角成(88)、２二成銀(31)、同　歩(23)
# 移動先は、マス目か、直前の指し手と同じマスを表す「同」で書く。「同」の後の全角空白はないこともある
_NORMAL_MOVE_PATTERN = re.compile(
    rf"(?:([{_FILES}])([{_RANKS}])|同　?)(?:{_BOARD_PIECE_NAMES})(成?)\(([1-9])([1-9])\)"
)

# 持ち駒を打つ手。例: ５五角打
_DROP_MOVE_PATTERN = re.compile(rf"([{_FILES}])([{_RANKS}])({'|'.join(_DROP_PIECE_KINDS)})打")


def parse_kif_move(text: str, previous_to: Square | None = None) -> Move:
    """KIF形式の指し手の部分を、指し手の型に変換する。

    手数や消費時間を含まない、指し手の部分だけを受け取る。
    駒の名前の後ろに「成」があれば成る手とし、成銀などの駒の名前に含まれる「成」とは区別する。
    盤上の駒を動かす手では、駒の名前は確かめるだけで残さず、盤面の駒と一致するかも確かめない。
    「同」は、直前の指し手の移動先を移動先とする。

    Args:
        text: KIF形式の指し手の部分。例えば `７六歩(77)`、`２二角成(88)`、`５五角打`、`同　歩(23)`。
        previous_to: 直前の指し手の移動先。「同」を解釈するときだけ使う。初手では `None`。

    Returns:
        盤上の駒を動かす手なら `NormalMove`、持ち駒を打つ手なら `DropMove`。

    Raises:
        ValueError: KIF形式の指し手として読めない場合、`不成` と書かれている場合、
            直前の指し手がないのに「同」と書かれている場合、または移動元と移動先が同じ場合。
    """
    if normal := _NORMAL_MOVE_PATTERN.fullmatch(text):
        to_file, to_rank, promote, from_file, from_rank = normal.groups()
        if to_file is not None:
            to_square = _parse_square(to_file, to_rank)
        elif previous_to is not None:
            to_square = previous_to
        else:
            msg = f"直前の指し手がないので「同」を解釈できません。text: {text!r}"
            raise ValueError(msg)
        return NormalMove(
            from_square=Square(file=int(from_file), rank=int(from_rank)),
            to_square=to_square,
            promote=promote == "成",
        )
    if drop := _DROP_MOVE_PATTERN.fullmatch(text):
        to_file, to_rank, name = drop.groups()
        return DropMove(square=_parse_square(to_file, to_rank), kind=_DROP_PIECE_KINDS[name])
    if "不成" in text:
        msg = f"KIFの仕様に「不成」はありません。成らない手は「成」を書きません。text: {text!r}"
        raise ValueError(msg)
    msg = f"KIF形式の指し手として読めません。text: {text!r}"
    raise ValueError(msg)


def _parse_square(file_char: str, rank_char: str) -> Square:
    """KIFの筋の全角数字と段の漢数字を、マス目に変換する。

    Args:
        file_char: 筋。`１` から `９` の全角数字。
        rank_char: 段。`一` から `九` の漢数字。

    Returns:
        マス目。
    """
    return Square(file=_FILES.index(file_char) + 1, rank=_RANKS.index(rank_char) + 1)


# 対応する手合割。平手以外は扱わない
_HANDICAP = "平手"

# 指し手一覧の見出し。例: 手数----指手---------消費時間--
_MOVES_HEADER_PATTERN = re.compile(r"手数-+指手-+(?:消費時間-*)?")

# 指し手の行。例: `   9 同　銀(68)        ( 0:00/00:00:06)`
# 手数、指し手、省略できる消費時間、変化があることを示す「+」の順に並ぶ。指し手は「同」の後の全角空白を含む
_MOVE_LINE_PATTERN = re.compile(r"\s*(\d+) +(\S+?(?:　\S+?)?)(?:\s+\([^)]*\))?\+?\s*")

# 指し手の行と同じ形で書く終局の言葉。KIFの仕様に挙がっているもの
_END_WORDS = frozenset(
    {
        "中断",
        "投了",
        "持将棋",
        "千日手",
        "切れ負け",
        "反則勝ち",
        "反則負け",
        "入玉勝ち",
        "不戦勝",
        "不戦敗",
        "詰み",
        "不詰",
    }
)

# ヘッダの行。例: 手合割：平手
_HEADER_PATTERN = re.compile(r"([^：]+)：(.*)")


@dataclass(frozen=True)
class KifGame:
    """KIF形式の棋譜から取り出した、本譜の内容。

    Attributes:
        handicap: 手合割。今は平手だけを扱う。
        moves: 本譜の指し手。初手から順に並ぶ。
    """

    handicap: str
    moves: tuple[Move, ...]


def read_kif(path: Path) -> KifGame:
    """KIF形式の棋譜ファイルを読み、本譜の内容を取り出す。

    UTF-8で読み、読めなければcp932で読む。UTF-8の先頭のBOMは取り除く。文字コードを判定するわけではない。

    Args:
        path: 棋譜ファイルのパス。

    Returns:
        本譜の内容。

    Raises:
        UnicodeDecodeError: UTF-8でもcp932でも読めない場合。
        ValueError: 棋譜として読めない場合。`parse_kif` と同じ。
    """
    raw = path.read_bytes()
    try:
        text = raw.decode("utf-8-sig")
    except UnicodeDecodeError:
        text = raw.decode("cp932")
    return parse_kif(text)


def parse_kif(text: str) -> KifGame:
    """KIF形式の棋譜の文字列から、手合割と本譜の指し手を取り出す。

    行ごとに次のように扱う。終局の行か `変化：` の行に来たら、その後ろは読まない。

    - 空行、`#` と `*` で始まるコメント、指し手一覧の見出しは読み飛ばす
    - `手合割：` は平手かを確かめる。省略されていれば、KIFの仕様に従って平手とする
    - それ以外の `キー：値` の行は読み捨てる
    - 指し手の行は、手数が1からの連番かを確かめて指し手に変換する

    Args:
        text: KIF形式の棋譜の文字列。

    Returns:
        本譜の内容。

    Raises:
        ValueError: 平手以外の手合割、手数が連番でない行、読めない指し手、
            `&` で始まるしおり、どの形式にも当てはまらない行がある場合。
    """
    moves: list[Move] = []
    previous_to: Square | None = None
    for line_number, number, move_text in _main_line_move_texts(text):
        if number != len(moves) + 1:
            msg = f"{line_number}行目: 手数が{len(moves) + 1}ではありません。number: {number}"
            raise ValueError(msg)
        if move_text in _END_WORDS:
            break
        try:
            move = parse_kif_move(move_text, previous_to)
        except ValueError as error:
            msg = f"{line_number}行目: {error}"
            raise ValueError(msg) from error
        moves.append(move)
        previous_to = move.to_square if isinstance(move, NormalMove) else move.square
    return KifGame(handicap=_HANDICAP, moves=tuple(moves))


def _main_line_move_texts(text: str) -> Iterator[tuple[int, int, str]]:
    """棋譜の文字列から、本譜の指し手の行を順に取り出す。

    指し手以外の行を確かめて読み飛ばし、`変化：` の行に来たら終える。終局の言葉も指し手として返す。

    Args:
        text: KIF形式の棋譜の文字列。

    Yields:
        行番号、手数、指し手の部分の組。

    Raises:
        ValueError: 平手以外の手合割、`&` で始まるしおり、どの形式にも当てはまらない行がある場合。
    """
    for line_number, line in enumerate(text.splitlines(), start=1):
        stripped = line.strip()
        if not stripped or stripped.startswith(("#", "*")) or _MOVES_HEADER_PATTERN.fullmatch(stripped):
            continue
        if stripped.startswith("変化："):
            return
        if stripped.startswith("&"):
            msg = f"{line_number}行目: しおりには対応していません。line: {line!r}"
            raise ValueError(msg)
        if move_line := _MOVE_LINE_PATTERN.fullmatch(line):
            number, move_text = move_line.groups()
            yield line_number, int(number), move_text
            continue
        if header := _HEADER_PATTERN.fullmatch(stripped):
            key, value = header.groups()
            if key == "手合割" and value.strip() != _HANDICAP:
                msg = f"{line_number}行目: 平手以外の手合割には対応していません。line: {line!r}"
                raise ValueError(msg)
            continue
        msg = f"{line_number}行目: KIF形式の行として読めません。line: {line!r}"
        raise ValueError(msg)
