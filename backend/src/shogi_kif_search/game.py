# Copyright (C) 2026 Said-Ay
# SPDX-License-Identifier: GPL-3.0-only

"""棋譜から各局面を生成する。"""

from dataclasses import dataclass
from typing import TYPE_CHECKING

from shogi_kif_search.position import Position
from shogi_kif_search.sfen import to_sfen
from shogi_kif_search.zobrist import calculate_hash, update_hash

if TYPE_CHECKING:
    from collections.abc import Iterator

    from shogi_kif_search.kif import KifGame


@dataclass(frozen=True)
class PositionRecord:
    """棋譜の1局面の記録。

    Attributes:
        move_number: 何手指した後の局面か。初期局面は0。
            「次が何手目か」を表す `Position.move_number` とは1ずれる。
        sfen: 局面のSFEN。
        hash_value: 局面のZobristハッシュ。
    """

    move_number: int
    sfen: str
    hash_value: int


def iter_positions(game: KifGame) -> Iterator[PositionRecord]:
    """棋譜から局面を順に取り出す。

    Args:
        game: 平手の初期局面から指した棋譜。

    Yields:
        初期局面から最後の指し手の後の局面まで、1局面ずつの記録。

    Raises:
        ValueError: 局面として起こりえない指し手がある場合。メッセージの先頭に何手目かを付ける。
    """
    position = Position.initial()
    hash_value = calculate_hash(position)
    yield _record(position, hash_value)
    for move_number, move in enumerate(game.moves, start=1):
        try:
            new_hash = update_hash(hash_value, position, move)
            position.push(move)
        except ValueError as error:
            msg = f"{move_number}手目: {error}"
            raise ValueError(msg) from error
        hash_value = new_hash
        yield _record(position, hash_value)


def _record(position: Position, hash_value: int) -> PositionRecord:
    """局面とそのハッシュから記録を作る。

    Args:
        position: 記録する局面。
        hash_value: 局面のZobristハッシュ。

    Returns:
        局面の記録。
    """
    # Position.move_number は次の手が何手目かを表すため1を引くと指した手の数になる
    return PositionRecord(
        move_number=position.move_number - 1,
        sfen=to_sfen(position),
        hash_value=hash_value,
    )
