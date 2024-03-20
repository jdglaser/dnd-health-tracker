from contextlib import asynccontextmanager
from typing import cast

import msgspec
from litestar import Litestar
from litestar.datastructures import State
from psycopg import AsyncConnection, AsyncCursor
from psycopg.rows import dict_row
from psycopg_pool import AsyncConnectionPool

from src import app_config
from src.exceptions import AppError

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


@asynccontextmanager
async def db_connection(app: Litestar):
    """
    Creates a context manager for providing a database connection pool

    The pool is stored within the application state.
    """
    conn_info = DatabaseConnInfo(
        host=app_config.DB_HOST,
        port=app_config.DB_PORT,
        username=app_config.DB_USER,
        password=app_config.DB_PASS,
        database=app_config.DB_DATABASE,
    )
    async with AsyncConnectionPool(conn_info.to_conn_str()) as pool:
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
    async with db_conn.cursor(row_factory=dict_row) as cur:
        yield cur
