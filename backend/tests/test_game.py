# Copyright (C) 2026 Said-Ay
# SPDX-License-Identifier: GPL-3.0-only

"""game.pyのテスト。"""

from pathlib import Path

from shogi_kif_search.game import iter_positions
from shogi_kif_search.kif import read_kif

GAME_001 = Path(__file__).parent / "data" / "game_001.kif"


def test_iter_positions() -> None:
    """テスト棋譜から局面を全部取り出せることを確認する。"""
    game = read_kif(GAME_001)
    positions = list(iter_positions(game))
    game_position_len = 77
    assert len(positions) == game_position_len
    assert positions[0].move_number == 0
    assert positions[-1].move_number == game_position_len - 1
