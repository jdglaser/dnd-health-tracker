from typing import Optional

import msgspec

from src.common.utils import CaseInsensitiveEnum


class CharacterClass(msgspec.Struct, frozen=True, kw_only=True, rename="camel"):
    name: str
    hit_dice_value: int
    class_level: int


class CharacterStats(msgspec.Struct, frozen=True, kw_only=True, rename="camel"):
    strength: int
    dexterity: int
    constitution: int
    intelligence: int
    wisdom: int
    charisma: int


class ItemModifier(msgspec.Struct, frozen=True, kw_only=True, rename="camel"):
    affected_object: str
    affected_value: str
    value: int


class Item(msgspec.Struct, frozen=True, kw_only=True, rename="camel"):
    name: str
    modifier: ItemModifier


class DamageType(CaseInsensitiveEnum):
    BLUDGEONING = "bludgeoning"
    PIERCING = "piercing"
    SLASHING = "slashing"
    FIRE = "fire"
    COLD = "cold"
    ACID = "acid"
    THUNDER = "thunder"
    LIGHTNING = "lightning"
    POISON = "poison"
    RADIANT = "radiant"
    NECROTIC = "necrotic"
    PSYCHIC = "psychic"
    FORCE = "force"


class DefenseType(CaseInsensitiveEnum):
    RESISTANCE = "resistance"
    IMMUNITY = "immunity"


class Defense(msgspec.Struct, frozen=True, kw_only=True, rename="camel"):
    damage_type: DamageType = msgspec.field(name="type")
    defense_type: DefenseType = msgspec.field(name="defense")


class CharacterHitpoints(msgspec.Struct, frozen=True, kw_only=True, rename="camel"):
    hit_point_max: int
    current_hit_points: int
    temporary_hit_points: Optional[int] = None


class Character(msgspec.Struct, frozen=True, kw_only=True, rename="camel"):
    name: str
    level: int
    hit_points: CharacterHitpoints
    classes: list[CharacterClass]
    stats: CharacterStats
    items: list[Item]
    defenses: list[Defense]


class DealDamageRequest(msgspec.Struct, frozen=True, kw_only=True, rename="camel"):
    amount: int
    damage_type: DamageType


class HealRequest(msgspec.Struct, frozen=True, kw_only=True, rename="camel"):
    amount: int


class AssignTemporaryHitPointsRequest(msgspec.Struct, frozen=True, kw_only=True, rename="camel"):
    amount: int
