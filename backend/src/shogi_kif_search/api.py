# Copyright (C) 2026 Said-Ay
# SPDX-License-Identifier: GPL-3.0-only

"""APIの処理を行う。"""

import os
import uuid
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Iterator
from functools import cache
from typing import Annotated, Literal

from fastapi import Depends, FastAPI, HTTPException
from pydantic import BaseModel
from sqlalchemy import Engine, create_engine, select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.orm import Session

from shogi_kif_search.db import Game, Move, Position, User, get_or_create_user
from shogi_kif_search.game import iter_positions
from shogi_kif_search.kif import KifGame, parse_kif
from shogi_kif_search.sfen import strip_move_number
from shogi_kif_search.usi import to_usi

app = FastAPI()


class GameCreateRequestSchema(BaseModel):
    """棋譜のアップロードのリクエストの本文。

    Attributes:
        kif: KIF形式の棋譜。
        my_side: 自分が先手なら `black`、後手なら `white`。
    """

    kif: str
    my_side: Literal["black", "white"]


class GameCreateResponseSchema(BaseModel):
    """棋譜のアップロードのレスポンス。

    Attributes:
        game_id: 登録した対局のID。
    """

    game_id: uuid.UUID


class MoveResponseSchema(BaseModel):
    """盤面の再生のレスポンスの1手分。

    Attributes:
        move_number: 何手目か。1から。
        move: USI形式の指し手。
        time_seconds: その手の消費時間。単位は秒。分からないときはNone。
        position_hash: その手を指した後の局面のハッシュ。16桁の16進数。
        sfen: その手を指した後の局面のSFEN。手数を除く。
    """

    move_number: int
    move: str
    time_seconds: int | None
    position_hash: str
    sfen: str


class GameMovesResponseSchema(BaseModel):
    """盤面の再生のレスポンス。

    Attributes:
        game_id: 対局のID。
        moves: 初手から順に並べた全手。
    """

    game_id: uuid.UUID
    moves: list[MoveResponseSchema]


@cache
def get_engine() -> Engine:
    """DBのエンジンを返す。"""
    return create_engine(os.environ["DATABASE_URL"])


def get_db() -> Iterator[Session]:
    """DBのセッションを返す。"""
    with Session(get_engine()) as session:
        yield session  # ①準備 → ②値を渡す → ③後片付け、の3段構成


@app.post("/api/games", status_code=201)
def create_game(
    request: GameCreateRequestSchema, session: Annotated[Session, Depends(get_db)]
) -> GameCreateResponseSchema:
    """棋譜をアップロードする。"""
    try:
        kif_game: KifGame = parse_kif(request.kif)
        # ジェネレータは取り出すときに局面を進めるので、不正な手をここで見つけるためにリストにする
        position_records = list(iter_positions(kif_game))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    user: User = get_or_create_user(session, "local")
    game: Game = Game(user_id=user.user_id, my_side=request.my_side, game_id=uuid.uuid4(), result="unknown")
    session.add(game)
    for record in position_records:
        if record.move_number == 0:
            continue  # 初期局面はDBに登録しない
        statement = (
            insert(Position)
            .values(position_hash=record.hash_value, sfen=strip_move_number(record.sfen))
            .on_conflict_do_nothing(index_elements=[Position.position_hash])
        )
        session.execute(statement)
        move = Move(
            game_id=game.game_id,
            move_number=record.move_number,
            move=to_usi(kif_game.moves[record.move_number - 1]),
            time_seconds=None,
            position_hash=record.hash_value,
        )
        session.add(move)
    session.commit()
    return GameCreateResponseSchema(game_id=game.game_id)


@app.get("/api/games/{game_id}/moves", response_model=GameMovesResponseSchema)
def get_game_moves(
    game_id: uuid.UUID, session: Annotated[Session, Depends(get_db)]
) -> GameMovesResponseSchema:
    """対局の全手を返す。"""
    game: Game | None = session.get(Game, game_id)
    if game is None:
        raise HTTPException(status_code=404, detail="Game not found")
    statement = (
        select(Move, Position.sfen)
        .join(Position, Move.position_hash == Position.position_hash)
        .where(Move.game_id == game_id)
        .order_by(Move.move_number)
    )
    rows = session.execute(statement).all()
    return GameMovesResponseSchema(
        game_id=game.game_id,
        moves=[
            MoveResponseSchema(
                move_number=move.move_number,
                move=move.move,
                time_seconds=move.time_seconds,
                position_hash=f"{move.position_hash:016x}",
                sfen=sfen,
            )
            for move, sfen in rows
        ],
    )
