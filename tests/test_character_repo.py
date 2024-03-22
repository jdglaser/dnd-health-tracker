import pytest

from src.character.character_repo import CharacterRepo
from src.character.exceptions import CharacterNotFoundException
from src.character.models import CharacterHitpoints


async def test_update_hitpoints(character_repo: CharacterRepo):
    # Get character
    character = await character_repo.get_character(1)
    hitpoints = character.hit_points
    assert hitpoints == CharacterHitpoints(hit_point_max=25, current_hit_points=25, temporary_hit_points=None)

    # Update hitpoints
    await character_repo.update_hitpoints(
        character_id=1, hitpoints=CharacterHitpoints(hit_point_max=20, current_hit_points=15, temporary_hit_points=5)
    )

    # Hitpoints should be updated
    character = await character_repo.get_character(1)
    assert character.hit_points == CharacterHitpoints(hit_point_max=20, current_hit_points=15, temporary_hit_points=5)


async def test_update_hitpoints_character_doesnt_exist(character_repo: CharacterRepo):
    # Try to update hitpoints of a character id that doesn't exist
    with pytest.raises(CharacterNotFoundException) as exc:
        await character_repo.update_hitpoints(
            character_id=2, hitpoints=CharacterHitpoints(hit_point_max=20, current_hit_points=15)
        )

    assert str(exc.value) == "Cannot find character with id 2"
