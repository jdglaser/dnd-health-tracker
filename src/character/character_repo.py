import msgspec
from psycopg import AsyncCursor

from src.character.exceptions import CharacterNotFoundException, CharacterRepoException
from src.character.models import (
    Character,
    CharacterClass,
    CharacterStats,
    Defense,
    Item,
    ItemModifier,
    TemporaryHitpoints,
)
from src.log_config import get_logger

LOG = get_logger(__name__)


class CharacterRepo:
    def __init__(self, db: AsyncCursor) -> None:
        self.db = db

    async def update_hitpoints(self, character_id: int): ...

    async def update_temporary_hitpoints(self, character_id: int, temporary_hitpoints: TemporaryHitpoints): ...

    async def get_character(self, character_id: int):
        character_res = await (
            await self.db.execute(
                """
                SELECT name, level, hit_points
                FROM operational.character
                WHERE id = %(id)s
                """,
                {"id": character_id},
            )
        ).fetchone()

        if not character_res:
            raise CharacterNotFoundException(f"Cannot find character for character id '{character_id}'")

        character_classes = await self.get_character_classes(character_id=character_id)
        character_stats = await self.get_character_stats(character_id=character_id)
        character_items = await self.get_character_items(character_id=character_id)
        character_defenses = await self.get_character_defenses(character_id=character_id)

        return Character(
            name=character_res["name"],
            level=character_res["level"],
            hit_points=character_res["hit_points"],
            classes=character_classes,
            stats=character_stats,
            items=character_items,
            defenses=character_defenses,
        )

    async def get_character_classes(self, character_id: int):
        res = await (
            await self.db.execute(
                """
                    SELECT class_name as name, hit_dice_value as "hitDiceValue", class_level as "classLevel"
                    FROM operational.character_class
                    WHERE character_id = %(id)s
                    """,
                {"id": character_id},
            )
        ).fetchall()
        return msgspec.convert(
            res,
            list[CharacterClass],
        )

    async def get_character_defenses(self, character_id: int):
        return msgspec.convert(
            await (
                await self.db.execute(
                    """
                    SELECT lower(damage_type) as type, defense_type as defense
                    FROM operational.character_defense
                    WHERE character_id = %(id)s
                    """,
                    {"id": character_id},
                )
            ).fetchall(),
            list[Defense],
        )

    async def get_character_stats(self, character_id: int):
        stats_res = await (
            await self.db.execute(
                """
                    SELECT stat, value
                    FROM operational.character_stat
                    WHERE character_id = %(id)s
                    """,
                {"id": character_id},
            )
        ).fetchall()

        if not stats_res:
            raise CharacterNotFoundException(f"Cannot find character stats for character id '{character_id}'")

        stat_dict = {r["stat"]: r["value"] for r in stats_res}
        return msgspec.convert(stat_dict, CharacterStats)

    async def get_character_items(self, character_id: int):
        item_res = await (
            await self.db.execute(
                """
                SELECT ci.id, ci.name, cim.affected_object as "affectedObject",
                cim.affected_value as "affectedValue", cim.value
                FROM operational.character_item ci
                JOIN operational.character_item_modifier cim ON ci.id = cim.character_item_id
                WHERE character_id = %(id)s
                """,
                {"id": character_id},
            )
        ).fetchall()

        if not item_res:
            return []

        items: list[Item] = []
        for item in item_res:
            items.append(
                Item(
                    name=item["name"],
                    modifier=ItemModifier(
                        affected_object=item["affectedObject"],
                        affected_value=item["affectedValue"],
                        value=item["value"],
                    ),
                )
            )

        return items

    async def insert_character(self, character: Character):
        LOG.info(f"Inserting character: {character}")
        character_id_res = await (
            await self.db.execute(
                """
                INSERT INTO operational.character
                (name, level, hit_points)
                VALUES
                (%(name)s, %(level)s, %(hit_points)s)
                RETURNING id
                """,
                {
                    "name": character.name,
                    "level": character.level,
                    "hit_points": character.hit_points,
                },
            )
        ).fetchone()

        if not character_id_res:
            raise CharacterRepoException(f"Unable to resolve inserted character ID for character: {character}")

        character_id = character_id_res[0]

        await self.insert_character_classes(character_id=character_id, classes=character.classes)
        await self.insert_character_stat(character_id=character_id, character_stats=character.stats)
        for item in character.items:
            await self.insert_character_item(character_id=character_id, character_item=item)
        await self.insert_character_defenses(character_id=character_id, defenses=character.defenses)

    async def insert_character_classes(self, character_id: int, classes: list[CharacterClass]):
        LOG.info(f"Inserting {len(classes)} character classes for character id {character_id}")
        await self.db.executemany(
            """
            INSERT INTO operational.character_class
            (character_id, class_name, hit_dice_value, class_level)
            VALUES
            (%(character_id)s, %(name)s, %(hit_dice_value)s, %(class_level)s)
            """,
            [{"character_id": character_id} | msgspec.structs.asdict(clazz) for clazz in classes],
        )

    async def insert_character_stat(self, character_id: int, character_stats: CharacterStats):
        LOG.info(f"Inserting character stats for character id {character_id}")
        await self.db.executemany(
            """
            INSERT INTO operational.character_stat
            (character_id, stat, value)
            VALUES
            (%(character_id)s, %(stat)s, %(value)s)
            """,
            [
                {"character_id": character_id, "stat": s, "value": v}
                for s, v in msgspec.structs.asdict(character_stats).items()
            ],
        )

    async def insert_character_item(self, character_id: int, character_item: Item):
        LOG.info(f"Inserting character item for character id {character_id}")
        item_id_res = await (
            await self.db.execute(
                """
                INSERT INTO operational.character_item
                (character_id, name) VALUES (%(character_id)s, %(name)s)
                RETURNING id
                """,
                {"character_id": character_id, "name": character_item.name},
            )
        ).fetchone()

        if not item_id_res:
            raise CharacterRepoException(f"Unable to resolve id for item {character_item}")

        item_id = item_id_res[0]

        LOG.info(f"Inserting character item modifier for character item id '{item_id}'")
        await self.db.execute(
            """
            INSERT INTO operational.character_item_modifier
            (character_item_id, affected_object, affected_value, value)
            VALUES
            (%(character_item_id)s, %(affected_object)s, %(affected_value)s, %(value)s)
            """,
            {"character_item_id": item_id} | msgspec.structs.asdict(character_item.modifier),
        )

    async def insert_character_defenses(self, character_id: int, defenses: list[Defense]):
        LOG.info(f"Inserting character defenses for character id {character_id}")
        await self.db.executemany(
            """
            INSERT INTO operational.character_defense
            (character_id, damage_type, defense_type) VALUES
            (%(character_id)s, %(damage_type)s, %(defense_type)s)
            """,
            [{"character_id": character_id} | msgspec.structs.asdict(defense) for defense in defenses],
        )
