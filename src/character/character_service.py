import math
from typing import Optional

import msgspec
from psycopg import AsyncCursor

from src.character.character_repo import CharacterRepo
from src.character.models import Character, DamageType, Defense, DefenseType
from src.common.log_config import get_logger
from src.common.utils import acquire_lock

LOG = get_logger(__name__)


class CharacterService:
    def __init__(self, character_repo: CharacterRepo, db: AsyncCursor) -> None:
        self.character_repo = character_repo
        self.db = db

    async def heal(self, character_id: int, heal_amount: int) -> Character:
        await acquire_lock(f"CharacterService__heal_{character_id}", self.db)
        character = await self.character_repo.get_character(1)
        new_hit_points = character.hit_points.current_hit_points + heal_amount

        character = await self.character_repo.update_hitpoints(
            1,
            msgspec.structs.replace(
                character.hit_points,
                current_hit_points=(
                    new_hit_points
                    if new_hit_points <= character.hit_points.hit_point_max
                    else character.hit_points.hit_point_max
                ),
            ),
        )

        return character

    async def assign_temporary_hit_points(self, character_id: int, amount: int) -> Character:
        """
        Assigns temporary hitpoints to the character. Has no effect if the amount is smaller than the character's
        current temporary hitpoints (if any)
        """
        await acquire_lock(f"CharacterService__assign_temporary_hit_points_{character_id}", self.db)
        character = await self.character_repo.get_character(character_id)

        temporary_hitpoints = character.hit_points.temporary_hit_points
        if temporary_hitpoints and temporary_hitpoints >= amount:
            return character

        new_hit_points = msgspec.structs.replace(character.hit_points, temporary_hit_points=amount)
        return await self.character_repo.update_hitpoints(character_id=character_id, hitpoints=new_hit_points)

    async def deal_damage(self, character_id: int, damage: int, damage_type: DamageType) -> Character:
        """
        Deals `damage` of `damage_type` to character taking into account defenses and temporary hitpoints
        """
        await acquire_lock(f"CharacterService__deal_damage_{character_id}", self.db)
        character = await self.character_repo.get_character(character_id=character_id)
        defense = self._resolve_defense(defenses=character.defenses, damage_type=damage_type)
        # If immune to the damage type, do no damage and return
        if defense and defense == DefenseType.IMMUNITY:
            return character

        remaining_damage = damage
        # If resistant to the damage type, cut remaining damage in half (rounding down)
        if defense and defense == DefenseType.RESISTANCE:
            remaining_damage = math.floor(remaining_damage / 2)

        # Resolve temporary hitpoints
        temporary_hitpoints = character.hit_points.temporary_hit_points
        if temporary_hitpoints:
            # If the temporary hitpoints is greater than or equal to the remaining damage, subtract the damage from
            # the temporary hitpoints, update the character, and return
            if remaining_damage <= temporary_hitpoints:
                new_temporary_hitpoints = (temporary_hitpoints - remaining_damage) or None
                return await self.character_repo.update_hitpoints(
                    character_id=character_id,
                    hitpoints=msgspec.structs.replace(
                        character.hit_points,
                        temporary_hit_points=new_temporary_hitpoints,
                    ),
                )

            remaining_damage -= temporary_hitpoints
            temporary_hitpoints = None

        # Subtract the remaining damage from the current hitpoints and update. If the current hitpoints drop below 0
        # set the value back to 0
        current_hit_points = character.hit_points.current_hit_points
        current_hit_points -= remaining_damage
        new_hit_points = msgspec.structs.replace(
            character.hit_points,
            current_hit_points=current_hit_points if current_hit_points >= 0 else 0,
            temporary_hit_points=temporary_hitpoints,
        )
        return await self.character_repo.update_hitpoints(character_id=character_id, hitpoints=new_hit_points)

    def _resolve_defense(self, defenses: list[Defense], damage_type: DamageType) -> Optional[DefenseType]:
        """
        If a defense to the `damage_type` is present in `defenses`, return the `DefenseType`, otherwise return `None`
        """
        for defense in defenses:
            if defense.damage_type == damage_type:
                return defense.defense_type
        return None
