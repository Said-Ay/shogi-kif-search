# Copyright (C) 2026 Said-Ay
# SPDX-License-Identifier: GPL-3.0-only

"""game.pyのテスト。"""

from typing import TYPE_CHECKING

from shogi_kif_search.game import iter_positions
from shogi_kif_search.kif import read_kif

if TYPE_CHECKING:
    from pathlib import Path

# 初期局面から76手目までの局面の数
EXPECTED_POSITIONS = 77


def test_iter_positions(game_001_path: Path) -> None:
    """テスト棋譜から局面を全部取り出せることを確認する。"""
    game = read_kif(game_001_path)
    positions = list(iter_positions(game))
    assert len(positions) == EXPECTED_POSITIONS
    assert positions[0].move_number == 0
    assert positions[-1].move_number == EXPECTED_POSITIONS - 1
