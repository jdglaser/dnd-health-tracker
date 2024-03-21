from typing import Any

import uvicorn
from litestar import Litestar, Router, get
from litestar.logging import LoggingConfig
from litestar.openapi import OpenAPIConfig, OpenAPIController

from src import app_config
from src.character.character_repo import CharacterRepo
from src.character.models import Character
from src.db import db_connection, insert_test_data, migrate_db, teardown_db
from src.deps import provide_dependencies
from src.exceptions import app_exception_handler


# Define primary health route
@get("/health")
async def health() -> dict[str, Any]:
    return {"status": "pass", "description": "Application is healthy", "environment": app_config.ENV}


@get("/test")
async def test_me(character_repo: CharacterRepo) -> Character:
    return await character_repo.get_character(1)


# Customize the path where OpenAPI docs live
class CustomOpenApiController(OpenAPIController):
    path = f"{app_config.API_BASE_URL}/docs"


# Main api router for the application
api_router = Router(app_config.API_BASE_URL, route_handlers=[health, test_me])

# Setup main application
app = Litestar(
    # Set main api router
    route_handlers=[api_router],
    # Make a DB connection pool available for the lifespan of the application
    lifespan=[db_connection],
    # Migrate db and insert test data on startup. Only insert test data in local dev
    on_startup=[migrate_db] + ([insert_test_data] if app_config.ENV == app_config.Environment.LOCAL_DEV else []),
    # Only run db teardown in local dev
    on_shutdown=[teardown_db] if app_config.ENV == app_config.Environment.LOCAL_DEV else [],
    # Setup dependencies
    dependencies=provide_dependencies(),
    # Base exception handler for application
    exception_handlers={Exception: app_exception_handler},
    # Customize OpenAPI configuration
    openapi_config=OpenAPIConfig(
        title=app_config.PROJECT_NAME, version=app_config.VERSION, openapi_controller=CustomOpenApiController
    ),
    # Turn off duplicative Litestar logging
    logging_config=LoggingConfig(root={"handlers": []}),
)

# When running locally with Python, we'll use this
if __name__ == "__main__":
    uvicorn.run("src.main:app", host="127.0.0.1", port=3000, reload=True)
