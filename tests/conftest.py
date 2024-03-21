import psycopg
import pytest

from src.db import get_conn_info, insert_test_data, migrate_db, teardown_db
from src.utils import dict_row_camel


@pytest.fixture(scope="module")
async def db():
    await teardown_db()
    await migrate_db()
    await insert_test_data()

    async with await psycopg.AsyncConnection.connect(get_conn_info().to_conn_str()) as conn:
        async with conn.cursor(row_factory=dict_row_camel) as cur:
            yield cur

    await teardown_db()
