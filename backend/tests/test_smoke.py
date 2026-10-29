# Copyright (C) 2026 Said-Ay
# SPDX-License-Identifier: GPL-3.0-only

"""スモークテスト。"""

from importlib.metadata import metadata

import cshogi

import shogi_kif_search


def test_smoke() -> None:
    """スモークテスト。shogi_kif_searchがインストールされてimportできるかを確認する。"""
    info = metadata("shogi_kif_search")
    assert info["Name"] == "shogi-kif-search"
    assert shogi_kif_search.__name__ == "shogi_kif_search"


def test_cshogi() -> None:
    """cshogiのメタデータが取得できるかを確認する。"""
    info = metadata("cshogi")
    assert info["Name"] == "cshogi"


def test_cshogi_sfen() -> None:
    """cshogiのsfen()が正しく動作するかを確認する。"""
    board = cshogi.Board()
    sfen = board.sfen()
    assert sfen == "lnsgkgsnl/1r5b1/ppppppppp/9/9/9/PPPPPPPPP/1B5R1/LNSGKGSNL b - 1"
