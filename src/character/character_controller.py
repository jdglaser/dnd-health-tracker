from litestar import Controller, get, put

from src.character.character_repo import CharacterRepo
from src.character.models import AssignTemporaryHitPointsRequest, Character, DealDamageRequest, HealRequest


class CharacterController(Controller):
    path = "/character/{id:int}"

    @get()
    async def get_character(self, id: int, character_repo: CharacterRepo) -> Character:
        return await character_repo.get_character(id)

    @put("/hit-points/damage")
    async def deal_damage(self, id: int, data: DealDamageRequest) -> Character: ...

    @put("/hit-points/heal")
    async def heal(self, id: int, data: HealRequest) -> Character: ...

    @put("/hit-points/temporary")
    async def assign_temporary_hit_points(self, id: int, temporary: AssignTemporaryHitPointsRequest) -> Character: ...
