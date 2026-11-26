# Copyright (C) 2026 Said-Ay
# SPDX-License-Identifier: GPL-3.0-only

"""api.pyのテスト。

PostgreSQLに対して動かす。環境変数 DATABASE_URL がなければ飛ばす。
各テストは1つのトランザクションの中で動き、終わったら取り消すので、DBにデータは残らない。
"""

import os
import uuid
from http import HTTPStatus
from typing import TYPE_CHECKING

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from shogi_kif_search.api import app, get_db, get_engine
from shogi_kif_search.db import Position

if TYPE_CHECKING:
    from collections.abc import Iterator
    from pathlib import Path

# game_001.kif の手数
GAME_001_MOVES = 76


@pytest.fixture
def session() -> Iterator[Session]:
    """テストが終わったら取り消すトランザクションの中のセッション。"""
    if not os.environ.get("DATABASE_URL"):
        pytest.skip("環境変数 DATABASE_URL がないので、APIのテストを飛ばす。")
    with get_engine().connect() as connection:
        transaction = connection.begin()
        # API の中の commit は、外側のトランザクションを確定させず、セーブポイントを確定させるだけにする
        session = Session(bind=connection, join_transaction_mode="create_savepoint")
        try:
            yield session
        finally:
            session.close()
            transaction.rollback()


@pytest.fixture
def client(session: Session) -> Iterator[TestClient]:
    """APIが使うセッションを、テスト用のセッションに差し替えたクライアント。"""
    app.dependency_overrides[get_db] = lambda: session
    try:
        yield TestClient(app)
    finally:
        app.dependency_overrides.clear()


def _count_positions(session: Session) -> int:
    """局面の表の行数を数える。"""
    return session.scalar(select(func.count()).select_from(Position)) or 0


def test_create_and_get_game(client: TestClient, game_001_path: Path) -> None:
    """棋譜を送ると201と対局のIDが返り、そのIDで全手を取り出せることを確認する。"""
    kif = game_001_path.read_text(encoding="utf-8")
    response = client.post("/api/games", json={"kif": kif, "my_side": "black"})
    assert response.status_code == HTTPStatus.CREATED

    game_id = response.json()["game_id"]
    response = client.get(f"/api/games/{game_id}/moves")
    assert response.status_code == HTTPStatus.OK
    assert len(response.json()["moves"]) == GAME_001_MOVES


def test_create_game_same_positions(client: TestClient, session: Session, game_001_path: Path) -> None:
    """同じ棋譜を2回送っても、局面の行が増えないことを確認する。"""
    kif = game_001_path.read_text(encoding="utf-8")
    client.post("/api/games", json={"kif": kif, "my_side": "black"})
    first_count = _count_positions(session)

    client.post("/api/games", json={"kif": kif, "my_side": "white"})
    assert _count_positions(session) == first_count


@pytest.mark.parametrize(
    "kif",
    [
        pytest.param("aaaaa", id="unreadable_line"),
        # 2手目を1手目で空いた７七から動かす。KIFとしては読めるが、局面を進めるときに分かる
        pytest.param("1 ７六歩(77)\n2 ７六歩(77)\n", id="impossible_move"),
    ],
)
def test_create_game_invalid_kif(client: TestClient, kif: str) -> None:
    """KIFとして受け付けられない棋譜は400になることを確認する。"""
    response = client.post("/api/games", json={"kif": kif, "my_side": "black"})
    assert response.status_code == HTTPStatus.BAD_REQUEST


def test_get_game_moves_not_found(client: TestClient) -> None:
    """ない対局のIDを指定すると404になることを確認する。"""
    response = client.get(f"/api/games/{uuid.uuid4()}/moves")
    assert response.status_code == HTTPStatus.NOT_FOUND
