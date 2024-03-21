from psycopg import AsyncCursor

from src.character.character_repo import CharacterRepo
from src.character.models import Character


class CharacterService:
    def __init__(self, character_repo: CharacterRepo, db: AsyncCursor) -> None:
        self.character_repo = character_repo

    def deal_damage(self, character_id: int, damage: int) -> Character: ...

    def heal(self, character_id: int, heal_amount: int) -> Character: ...

    def assign_temporary_hit_points(self, character_id: int, amount: int) -> Character: ...
