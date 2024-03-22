import json
from contextlib import asynccontextmanager
from pathlib import Path
from typing import cast

import msgspec
import psycopg
from litestar import Litestar
from litestar.datastructures import State
from psycopg import AsyncConnection, AsyncCursor, Cursor
from psycopg_pool import AsyncConnectionPool

from src.character.character_repo import CharacterRepo
from src.character.models import Character
from src.common import app_config
from src.common.app_error import AppError
from src.common.log_config import get_logger
from src.common.utils import dict_row_camel

LOG = get_logger(__name__)

# Type aliases for convenience
DbConn = AsyncConnection
DB = AsyncCursor


# Database configuration convenience class
class DatabaseConnInfo(msgspec.Struct, frozen=True, kw_only=True):
    host: str
    port: int
    username: str
    password: str
    database: str

    def to_conn_str(self):
        return (
            f"host={self.host} port={self.port} user={self.username} "
            f"password={self.password} dbname={self.database}"
        )


def get_conn_info() -> DatabaseConnInfo:
    """
    Helper function to get database connection info
    """
    return DatabaseConnInfo(
        host=app_config.DB_HOST,
        port=app_config.DB_PORT,
        username=app_config.DB_USER,
        password=app_config.DB_PASS,
        database=app_config.DB_DATABASE,
    )


@asynccontextmanager
async def db_connection(app: Litestar):
    """
    Creates a context manager for providing a database connection pool

    The pool is stored within the application state.
    """
    async with AsyncConnectionPool(get_conn_info().to_conn_str()) as pool:
        app.state.pool = pool
        yield pool


async def provide_db_conn(state: State):
    """
    Provides a database connection from the connection pool stored in the application state
    """
    if "pool" not in state:
        raise AppError("Cannot find connection pool in application state")

    connection_pool = cast(AsyncConnectionPool, state.pool)
    async with connection_pool.connection() as conn:
        yield conn


async def provide_db(db_conn: AsyncConnection):
    """
    Provides a database cursor object from a database connection object
    """
    async with db_conn.cursor(row_factory=dict_row_camel) as cur:
        yield cur


async def insert_test_data():
    """
    App startup function for inserting initial data
    """
    with open(app_config.TEST_DATA_PATH, "r") as fp:
        test_data = json.load(fp)

    test_data["hitPoints"] = {"hitPointMax": test_data["hitPoints"], "currentHitPoints": test_data["hitPoints"]}

    character = msgspec.convert(test_data, Character)
    async with await psycopg.AsyncConnection.connect(get_conn_info().to_conn_str()) as conn:
        async with conn.cursor(row_factory=dict_row_camel) as cur:
            character_repo = CharacterRepo(cur)
            await character_repo.insert_character(character=character)


def run_migration_script(path: Path, cur: Cursor):
    """
    Run the migration script at `path`
    """
    LOG.info(f"Executing migration '{path.name}'")
    with open(path, "r") as fp:
        for statement in fp.read().split(";"):
            cur.execute(statement)  # type: ignore


# In a real app, we'd use a database migration tool like Flyway to run proper migrations, but for this exercise, a
# simple setup and teardown script will do
async def migrate_db():
    """
    App startup function to setup the db
    """
    with psycopg.connect(get_conn_info().to_conn_str()) as conn:
        with conn.cursor() as cur:
            run_migration_script(app_config.MIGRATION_PATH / "setup.sql", cur)


async def teardown_db():
    """
    App shutdown function to teardown the db
    """
    with psycopg.connect(get_conn_info().to_conn_str()) as conn:
        with conn.cursor() as cur:
            run_migration_script(app_config.MIGRATION_PATH / "teardown.sql", cur)
