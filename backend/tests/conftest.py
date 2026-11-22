# Copyright (C) 2026 Said-Ay
# SPDX-License-Identifier: GPL-3.0-only

"""テストで共通に使う fixture。"""

from pathlib import Path

import pytest


@pytest.fixture
def game_001_path() -> Path:
    """全76手のテスト用の棋譜 `game_001.kif` のパス。"""
    return Path(__file__).parent / "data" / "game_001.kif"
