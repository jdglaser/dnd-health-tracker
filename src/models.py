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


class Defense(msgspec.Struct, frozen=True, kw_only=True, rename="camel"):
    damage_type: str = msgspec.field(name="type")
    defense_type: str = msgspec.field(name="defense")


class Character(msgspec.Struct, frozen=True, kw_only=True, rename="camel"):
    name: str
    level: int
    hit_points: int
    classes: list[CharacterClass]
    stats: CharacterStats
    items: list[Item]
    defenses: list[Defense]
