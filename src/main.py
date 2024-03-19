from contextlib import asynccontextmanager
from typing import AsyncGenerator

from litestar import Litestar, Router
from psycopg_pool import ConnectionPool

from src import app_config

api_router = Router("/api", route_handlers=[])


@asynccontextmanager
async def db_connection(app: Litestar):
    with ConnectionPool(
        f"postgresql+asyncpg://{app_config.DB_USER}:{app_config.DB_PASS}@{app_config.DB_HOST}:{app_config.DB_PORT}/postgres"
    ) as pool:
        app.state.pool = pool
        yield pool


app = Litestar(route_handlers=[api_router], lifespan=[db_connection])
