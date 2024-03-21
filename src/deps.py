from litestar.di import Provide

from src.character.character_repo import CharacterRepo
from src.db import provide_db, provide_db_conn


def provide_dependencies():
    return {
        "db_conn": Provide(provide_db_conn),
        "db": Provide(provide_db),
        "character_repo": Provide(CharacterRepo, sync_to_thread=False),
    }
