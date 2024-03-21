# Environment
import logging
import os
from enum import Enum
from pathlib import Path


class Environment(Enum):
    LOCAL_DEV = "local_dev"
    INT = "int"
    QA = "qa"
    PROD = "prod"


ENV = Environment(os.getenv("APP_ENV", "local_dev"))

LOG_LEVEL = logging.INFO
PROJECT_NAME = "dnd-health-tracker"
VERSION = "1.0.0"
API_MAJOR_VERSION = f"v{VERSION.split('.')[0]}"
API_BASE_URL = f"/api/{API_MAJOR_VERSION}"
MIGRATION_PATH = Path("./migrations")
TEST_DATA_PATH = Path("./briv.json")


# DB connection info
DB_USER = "postgres"
DB_PASS = "postgres"
DB_HOST = "localhost"
DB_PORT = 5432
DB_DATABASE = "postgres"
