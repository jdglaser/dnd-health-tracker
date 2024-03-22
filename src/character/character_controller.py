from litestar import Controller, get, put

from src.character.character_repo import CharacterRepo
from src.character.character_service import CharacterService
from src.character.models import AssignTemporaryHitPointsRequest, Character, DealDamageRequest, HealRequest


class CharacterController(Controller):
    path = "/character/{id:int}"

    @get()
    async def get_character(self, id: int, character_repo: CharacterRepo) -> Character:
        """
        Retrieve character data
        """
        return await character_repo.get_character(id)

    @put("/hit-points/damage")
    async def deal_damage(self, id: int, data: DealDamageRequest, character_service: CharacterService) -> Character:
        """
        Deal damage of a specific type to a character
        """
        return await character_service.deal_damage(character_id=id, damage=data.amount, damage_type=data.damage_type)

    @put("/hit-points/heal")
    async def heal(self, id: int, data: HealRequest, character_service: CharacterService) -> Character:
        """
        Heal a character
        """
        return await character_service.heal(character_id=id, heal_amount=data.amount)

    @put("/hit-points/temporary")
    async def assign_temporary_hit_points(
        self, id: int, data: AssignTemporaryHitPointsRequest, character_service: CharacterService
    ) -> Character:
        """
        Assign temporary hit points to a character
        """
        return await character_service.assign_temporary_hit_points(character_id=id, amount=data.amount)
