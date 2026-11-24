# Copyright (C) 2026 Said-Ay
# SPDX-License-Identifier: GPL-3.0-only

"""USIエンジンで局面を解析する。

cshogi を直接 import するのはこのモジュールのみとする。
"""

from dataclasses import dataclass
from typing import TYPE_CHECKING, Self

from cshogi.usi import Engine, InfoListener

if TYPE_CHECKING:
    from pathlib import Path
    from types import TracebackType


@dataclass(frozen=True)
class EngineAnalysis:
    """1局面の解析結果。

    評価値と詰みの手数は、解析した局面の手番の側から見た値。
    `score_cp` と `mate` は、どちらか一方だけが入る。

    Attributes:
        bestmove: 最善手。USI形式の指し手か、投了を表す `resign`、入玉宣言勝ちを表す `win`。
        score_cp: センチポーン単位の評価値。詰みのときや評価値がないときは None。
        mate: 詰みまでの手数。正なら手番の側が詰ませ、負なら詰まされる。
            すでに詰まされている局面では -1。詰みでないときは None。
        pv: 読み筋。USI形式の指し手だけを順に並べ、`resign` と `win` は含めない。
            すでに詰まされている局面などでは空。
    """

    bestmove: str
    score_cp: int | None
    mate: int | None
    pv: tuple[str, ...]


NODES = 1_000_000

# 起動したときに設定するオプション
_OPTIONS = {
    "Threads": "1",
    "USI_OwnBook": "false",
    "FV_SCALE": "24",
    "USI_Hash": "256",
}

# 最善手や読み筋に現れるが、指し手ではない言葉
_NON_MOVES = frozenset({"resign", "win"})


class UsiEngine:
    """USIエンジンを1回だけ起動し、複数の局面を解析する。

    `with` 文で使い、抜けるときにエンジンを終了する。
    """

    def __init__(self, path: Path) -> None:
        """エンジンの実行ファイルのパスを受け取る。"""
        self.path = path
        self._engine: Engine | None = None

    def __enter__(self) -> Self:
        """エンジンを起動。"""
        self._engine = Engine(str(self.path))
        for name, value in _OPTIONS.items():
            self._engine.setoption(name, value)
        self._engine.isready()
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_value: BaseException | None,
        traceback: TracebackType | None,
    ) -> None:
        """エンジンを終了する。"""
        if self._engine is not None:
            self._engine.quit()

    def analyze(self, sfen: str) -> EngineAnalysis:
        """SFENで表した局面を解析する。

        Args:
            sfen: 解析する局面のSFEN。

        Returns:
            最善手と、手番の側から見た評価値または詰みの手数、読み筋。

        Raises:
            RuntimeError: `with` 文の外で呼ばれた場合。
        """
        if self._engine is None:
            msg = "UsiEngine は with 文の中で使ってください。"
            raise RuntimeError(msg)

        self._engine.position(sfen=f"sfen {sfen}")
        info_listener = InfoListener()
        bestmove, _ = self._engine.go(nodes=NODES, listener=info_listener.listen())

        info = info_listener.info
        if info is None:
            return EngineAnalysis(bestmove=bestmove, score_cp=None, mate=None, pv=())

        # info の値は cshogi の Any なので型を確定させてから使う
        cp = info.get("cp")
        mate = info.get("mate")
        return EngineAnalysis(
            bestmove=bestmove,
            score_cp=cp if isinstance(cp, int) else None,
            mate=mate if isinstance(mate, int) else None,
            pv=tuple(str(move) for move in info.get("pv", []) if move not in _NON_MOVES),
        )
