from litestar.di import Provide

from src.db import provide_db, provide_db_conn


def provide_dependencies():
    return {
        "db_conn": Provide(provide_db_conn),
        "db": Provide(provide_db),
    }
