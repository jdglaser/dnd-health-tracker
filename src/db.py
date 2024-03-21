import json
from contextlib import asynccontextmanager
from pathlib import Path
from typing import cast

import msgspec
import psycopg
from litestar import Litestar
from litestar.datastructures import State
from msgspec.structs import asdict
from psycopg import AsyncConnection, AsyncCursor, Cursor
from psycopg.rows import dict_row
from psycopg_pool import AsyncConnectionPool

from src import app_config
from src.exceptions import AppError
from src.log_config import get_logger
from src.models import Character

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
    Quick helper function to get database connection info
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
    async with db_conn.cursor(row_factory=dict_row) as cur:
        yield cur


def insert_character(character: Character, cur: Cursor):
    """
    In a real app, we'd have various repo level classes to handle this kind of insert logic, but for the purpose of this
    exercise, we are only focusing on health tracking. So we will use this quick helper function to insert the starting
    data instead.
    """
    LOG.info("Inserting 'character'")
    character_id_res = cur.execute(
        """
        INSERT INTO operational.character
        (name, level, hit_points)
        VALUES
        (%(name)s, %(level)s, %(hit_points)s)
        RETURNING id
        """,
        {
            "name": character.name,
            "level": character.level,
            "hit_points": character.hit_points,
        },
    ).fetchone()

    if not character_id_res:
        raise AppError(f"Unable to resolve inserted character ID for character: {character}")

    character_id = character_id_res[0]

    LOG.info("Inserting 'character_class'")
    cur.executemany(
        """
        INSERT INTO operational.character_class
        (character_id, class_name, hit_dice_value, class_level)
        VALUES
        (%(character_id)s, %(name)s, %(hit_dice_value)s, %(class_level)s)
        """,
        [{"character_id": character_id} | asdict(clazz) for clazz in character.classes],
    )

    LOG.info("Inserting 'character_stat'")
    cur.executemany(
        """
        INSERT INTO operational.character_stat
        (character_id, stat, value)
        VALUES
        (%(character_id)s, %(stat)s, %(value)s)
        """,
        [{"character_id": character_id, "stat": s, "value": v} for s, v in asdict(character.stats).items()],
    )

    LOG.info("Inserting 'item'")
    for item in character.items:
        item_id_res = cur.execute(
            """
            INSERT INTO operational.item
            (name) VALUES (%(name)s)
            RETURNING id
            """,
            {"character_id": character_id, "name": item.name},
        ).fetchone()

        if not item_id_res:
            raise AppError(f"Unable to resolve id for item {item}")

        item_id = item_id_res[0]

        LOG.info(f"Inserting 'item_modifier' for item id '{item_id}'")
        cur.execute(
            """
            INSERT INTO operational.item_modifier
            (item_id, affected_object, affected_value, value)
            VALUES
            (%(item_id)s, %(affected_object)s, %(affected_value)s, %(value)s)
            """,
            {"item_id": item_id} | asdict(item.modifier),
        )

        LOG.info(f"Inserting 'character_item' for item id '{item_id}'")
        cur.execute(
            """
            INSERT INTO operational.character_item
            (character_id, item_id) VALUES (%(character_id)s, %(item_id)s)
            """,
            {"character_id": character_id, "item_id": item_id},
        )

    LOG.info("Inserting character_defense")
    cur.executemany(
        """
        INSERT INTO operational.character_defense
        (character_id, damage_type, defense_type) VALUES
        (%(character_id)s, %(damage_type)s, %(defense_type)s)
        """,
        [{"character_id": character_id} | asdict(defense) for defense in character.defenses],
    )


def insert_test_data(app: Litestar):
    """
    App startup function for inserting initial data
    """
    with open(app_config.TEST_DATA_PATH, "r") as fp:
        test_data = json.load(fp)

    character = msgspec.convert(test_data, Character)
    with psycopg.connect(get_conn_info().to_conn_str()) as conn:
        with conn.cursor() as cur:
            insert_character(character, cur)


def run_migration_script(path: Path, cur: Cursor):
    """
    Run the migration script at `path`
    """
    LOG.info(f"Executing migration '{path.name}'")
    with open(path, "r") as fp:
        for statement in fp.read().split(";"):
            cur.execute(statement)  # type: ignore


async def migrate_db(app: Litestar):
    """
    In a real app, we'd use a database migration tool like Flyway to run proper migrations, but for this exercise, a
    simple setup and teardown script will do
    """
    with psycopg.connect(get_conn_info().to_conn_str()) as conn:
        with conn.cursor() as cur:
            run_migration_script(app_config.MIGRATION_PATH / "setup.sql", cur)


def teardown_db(app: Litestar):
    """
    App shutdown function to teardown the db
    """
    with psycopg.connect(get_conn_info().to_conn_str()) as conn:
        with conn.cursor() as cur:
            run_migration_script(app_config.MIGRATION_PATH / "teardown.sql", cur)
