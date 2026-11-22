# Copyright (C) 2026 Said-Ay
# SPDX-License-Identifier: GPL-3.0-only

"""engine.pyのテスト。"""

import os
from pathlib import Path
from typing import TYPE_CHECKING

import pytest

from shogi_kif_search.engine import UsiEngine

if TYPE_CHECKING:
    from collections.abc import Iterator

INITIAL_SFEN = "lnsgkgsnl/1r5b1/ppppppppp/9/9/9/PPPPPPPPP/1B5R1/LNSGKGSNL b - 1"

# 後手番で、後手の玉が１一で金に詰まされている局面
MATED_SFEN = "8k/8G/8P/9/9/9/9/9/K8 w - 2"


@pytest.fixture(scope="module")
def engine() -> Iterator[UsiEngine]:
    """エンジンを1回だけ起動し、このモジュールのテストで使い回す。"""
    path = os.environ.get("ENGINE_PATH")
    if not path:
        pytest.skip("環境変数 ENGINE_PATH がないので、エンジンのテストを飛ばす。")
    with UsiEngine(Path(path)) as usi_engine:
        yield usi_engine


def test_analyze(engine: UsiEngine) -> None:
    """初期局面を解析すると、最善手と評価値が取れることを確認する。"""
    analysis = engine.analyze(INITIAL_SFEN)

    assert analysis.bestmove == analysis.pv[0]
    assert isinstance(analysis.score_cp, int)
    assert analysis.mate is None


def test_analyze_mated(engine: UsiEngine) -> None:
    """詰まされている局面では、投了になり、読み筋が空になることを確認する。"""
    analysis = engine.analyze(MATED_SFEN)

    assert analysis.bestmove == "resign"
    assert analysis.mate == -1
    assert analysis.pv == ()
