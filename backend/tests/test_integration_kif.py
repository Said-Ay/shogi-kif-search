# Copyright (C) 2026 Said-Ay
# SPDX-License-Identifier: GPL-3.0-only

"""棋譜変換の統合テスト。"""

from pathlib import Path

import cshogi
import pytest

from shogi_kif_search.kif import read_kif
from shogi_kif_search.position import Position
from shogi_kif_search.sfen import to_sfen

DATA_DIR = Path(__file__).parent / "data"
KIF_FILES = sorted(DATA_DIR.glob("*.kif"))

assert KIF_FILES, "テスト用のKIFファイルがありません。"


@pytest.mark.parametrize("kif_path", KIF_FILES, ids=lambda p: p.name)
def test_kif_conversion(kif_path: Path) -> None:
    """KIF形式の棋譜を読み込み、SFEN形式に変換して自作変換とcshogiの変換を比較する。"""
    my_kif_data = read_kif(kif_path)
    kif_text = kif_path.read_text(encoding="utf-8-sig")
    cshogi_kif_data = cshogi.KIF.Parser.parse_str(kif_text)
    my_position = Position.initial()
    cshogi_board = cshogi.Board()
    assert to_sfen(my_position) == cshogi_board.sfen()
    assert len(my_kif_data.moves) == len(cshogi_kif_data.moves), (
        f"{kif_path.name}: 指し手数が一致しません。"
        f"自作={len(my_kif_data.moves)}、"
        f"cshogi={len(cshogi_kif_data.moves)}"
    )
    for move_number, (my_move, cshogi_move) in enumerate(
        zip(my_kif_data.moves, cshogi_kif_data.moves, strict=True),
        start=1,
    ):
        my_position.push(my_move)
        cshogi_board.push(cshogi_move)

        assert to_sfen(my_position) == cshogi_board.sfen(), (
            f"{kif_path.name}: {move_number}手目でSFENが一致しません。"
        )
