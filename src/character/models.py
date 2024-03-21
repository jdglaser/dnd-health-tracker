from enum import Enum
from typing import Optional

import msgspec


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


class DamageType(Enum):
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


class Defense(msgspec.Struct, frozen=True, kw_only=True, rename="camel"):
    damage_type: DamageType = msgspec.field(name="type")
    defense_type: str = msgspec.field(name="defense")


class TemporaryHitpoints(msgspec.Struct, frozen=True, kw_only=True, rename="camel"):
    max_value: int
    current_value: int


class Character(msgspec.Struct, frozen=True, kw_only=True, rename="camel"):
    name: str
    level: int
    hit_points: int
    temporary_hitpoints: Optional[TemporaryHitpoints] = None
    classes: list[CharacterClass]
    stats: CharacterStats
    items: list[Item]
    defenses: list[Defense]
