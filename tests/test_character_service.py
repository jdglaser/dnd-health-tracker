from src.character.character_repo import CharacterRepo
from src.character.character_service import CharacterService
from src.character.models import DamageType


async def test_deal_damage(character_service: CharacterService, character_repo: CharacterRepo):
    character = await character_repo.get_character(1)
    assert character.hit_points.current_hit_points == 25

    character = await character_service.deal_damage(character_id=1, damage=5, damage_type=DamageType.COLD)

    assert character.hit_points.current_hit_points == 20


async def test_deal_damage_with_resistance(character_service: CharacterService, character_repo: CharacterRepo):
    character = await character_repo.get_character(1)
    assert character.hit_points.current_hit_points == 25

    character = await character_service.deal_damage(character_id=1, damage=5, damage_type=DamageType.SLASHING)

    assert character.hit_points.current_hit_points == 23


async def test_deal_damage_with_immunity(character_service: CharacterService, character_repo: CharacterRepo):
    character = await character_repo.get_character(1)
    assert character.hit_points.current_hit_points == 25

    character = await character_service.deal_damage(character_id=1, damage=5, damage_type=DamageType.FIRE)

    assert character.hit_points.current_hit_points == 25


async def test_assign_temporary_hit_points(character_service: CharacterService, character_repo: CharacterRepo):
    character = await character_repo.get_character(1)
    assert character.hit_points.temporary_hit_points is None

    character = await character_service.assign_temporary_hit_points(1, 5)
    assert character.hit_points.temporary_hit_points == 5


async def test_assign_temporary_hit_points_no_effect(character_service: CharacterService):
    # Assigning temporary hit points with a value smaller than current temporary hit points should have no effect
    character = await character_service.assign_temporary_hit_points(1, 5)

    assert character.hit_points.temporary_hit_points == 5

    character = await character_service.assign_temporary_hit_points(1, 4)

    assert character.hit_points.temporary_hit_points == 5


async def test_assign_temporary_hit_points_larger(character_service: CharacterService):
    # Assigning temporary hit points with a value greater than current temporary hit points should have an effect
    character = await character_service.assign_temporary_hit_points(1, 5)

    assert character.hit_points.temporary_hit_points == 5

    character = await character_service.assign_temporary_hit_points(1, 6)

    assert character.hit_points.temporary_hit_points == 6


async def test_deal_damage_with_temporary_hit_points_equal(character_service: CharacterService):
    character = await character_service.assign_temporary_hit_points(1, 5)

    # Damage is the same as temporary hit points
    character = await character_service.deal_damage(1, 5, DamageType.COLD)

    assert character.hit_points.current_hit_points == 25
    assert character.hit_points.temporary_hit_points is None


async def test_deal_damage_with_temporary_hit_points_less_than(character_service: CharacterService):
    character = await character_service.assign_temporary_hit_points(1, 5)

    # Damage is less than temporary hit points
    character = await character_service.deal_damage(1, 3, DamageType.COLD)

    assert character.hit_points.current_hit_points == 25
    assert character.hit_points.temporary_hit_points == 2


async def test_deal_damage_with_temporary_hit_points_greater(character_service: CharacterService):
    character = await character_service.assign_temporary_hit_points(1, 5)

    # Damage is greater than temporary hit points
    character = await character_service.deal_damage(1, 8, DamageType.COLD)

    assert character.hit_points.current_hit_points == 22
    assert character.hit_points.temporary_hit_points is None


async def test_heal(character_service: CharacterService):
    character = await character_service.deal_damage(1, 5, DamageType.COLD)

    assert character.hit_points.current_hit_points == 20

    character = await character_service.heal(1, 3)

    assert character.hit_points.current_hit_points == 23


async def test_heal_over_max(character_service: CharacterService):
    # Healing more than max health should not send current hit points over hit point max
    character = await character_service.deal_damage(1, 5, DamageType.COLD)

    assert character.hit_points.current_hit_points == 20

    character = await character_service.heal(1, 8)

    assert character.hit_points.current_hit_points == 25


async def test_heal_no_effect(character_service: CharacterService):
    # Healing full hit points does nothing
    character = await character_service.heal(1, 8)

    assert character.hit_points.current_hit_points == 25


async def test_heal_no_effect_temporary_hit_points(character_service: CharacterService):
    # Healing should not effect temporary hit points
    character = await character_service.deal_damage(1, 3, DamageType.BLUDGEONING)
    assert character.hit_points.current_hit_points == 22

    character = await character_service.assign_temporary_hit_points(1, 5)
    assert character.hit_points.temporary_hit_points == 5

    character = await character_service.heal(1, 2)

    assert character.hit_points.current_hit_points == 24
    assert character.hit_points.temporary_hit_points == 5
