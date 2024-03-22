import psycopg
import pytest
from psycopg import AsyncCursor

from src.character.character_repo import CharacterRepo
from src.character.character_service import CharacterService
from src.db import get_conn_info, insert_test_data, migrate_db, teardown_db
from src.utils import dict_row_camel


@pytest.fixture
async def db():
    await teardown_db()
    await migrate_db()
    await insert_test_data()

    async with await psycopg.AsyncConnection.connect(get_conn_info().to_conn_str()) as conn:
        async with conn.cursor(row_factory=dict_row_camel) as cur:
            yield cur

    await teardown_db()


@pytest.fixture
def character_repo(db: AsyncCursor):
    return CharacterRepo(db)


@pytest.fixture
def character_service(character_repo: CharacterRepo, db: AsyncCursor):
    return CharacterService(character_repo=character_repo, db=db)
