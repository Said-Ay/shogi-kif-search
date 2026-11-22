# Copyright (C) 2026 Said-Ay
# SPDX-License-Identifier: GPL-3.0-only

"""cli.pyのテスト。"""

from typing import TYPE_CHECKING

from shogi_kif_search.cli import main

if TYPE_CHECKING:
    from pathlib import Path

    import pytest

# 見出しの1行と初期局面から76手目までの77局面
EXPECTED_LINES = 78


def test_main(game_001_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    """棋譜の全局面を、見出し付きのTSVで1局面1行ずつ出力することを確認する。"""
    assert main([str(game_001_path)]) == 0

    lines = capsys.readouterr().out.splitlines()
    assert len(lines) == EXPECTED_LINES
    assert lines[0] == "move\tsfen\thash"


def test_main_invalid_move(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    """不正な手のある棋譜は手数を標準エラー出力に書いて終了コード1になることを確認する。"""
    path = tmp_path / "bad.kif"
    # 2手目を1手目で空いた７七から動かす
    path.write_text("1 ７六歩(77)\n2 ７六歩(77)\n", encoding="utf-8")

    assert main([str(path)]) == 1

    captured = capsys.readouterr()
    assert not captured.out
    assert "2手目" in captured.err
