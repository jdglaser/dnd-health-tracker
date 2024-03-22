import msgspec
from psycopg import AsyncCursor

from src.character.exceptions import CharacterNotFoundException, CharacterRepoException
from src.character.models import (
    Character,
    CharacterClass,
    CharacterHitpoints,
    CharacterStats,
    Defense,
    Item,
    ItemModifier,
)
from src.common.log_config import get_logger

LOG = get_logger(__name__)


class CharacterRepo:
    def __init__(self, db: AsyncCursor) -> None:
        self.db = db

    async def update_hitpoints(self, character_id: int, hitpoints: CharacterHitpoints) -> Character:
        updated_res = await (
            await self.db.execute(
                """
                UPDATE operational.character_hitpoints
                SET current_hit_points = %(current_hit_points)s,
                    hit_point_max = %(hit_point_max)s,
                    temporary_hit_points = %(temporary_hit_points)s
                WHERE id = %(character_id)s
                RETURNING id
                """,
                {"character_id": character_id} | msgspec.structs.asdict(hitpoints),
            )
        ).fetchone()

        if not updated_res:
            raise CharacterNotFoundException(f"Cannot find character with id {character_id}", character_id=character_id)

        return await self.get_character(character_id=character_id)

    async def get_character(self, character_id: int):
        character_res = await (
            await self.db.execute(
                """
                SELECT name,
                    level,
                    hit_point_max,
                    current_hit_points,
                    temporary_hit_points
                FROM operational.character c
                JOIN operational.character_hitpoints ch ON c.id = ch.character_id
                WHERE c.id = %(id)s
                """,
                {"id": character_id},
            )
        ).fetchone()

        if not character_res:
            raise CharacterNotFoundException(
                f"Cannot find character for character id {character_id}", character_id=character_id
            )

        character_classes = await self.get_character_classes(character_id=character_id)
        character_stats = await self.get_character_stats(character_id=character_id)
        character_items = await self.get_character_items(character_id=character_id)
        character_defenses = await self.get_character_defenses(character_id=character_id)

        name, level = character_res.pop("name"), character_res.pop("level")
        return Character(
            name=name,
            level=level,
            hit_points=msgspec.convert(character_res, CharacterHitpoints),
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
                    SELECT damage_type as type, defense_type as defense
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
            raise CharacterNotFoundException(
                f"Cannot find character stats for character id {character_id}", character_id=character_id
            )

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
                (name, level)
                VALUES
                (%(name)s, %(level)s)
                RETURNING id
                """,
                {
                    "name": character.name,
                    "level": character.level,
                },
            )
        ).fetchone()

        if not character_id_res:
            raise CharacterRepoException(f"Unable to resolve inserted character ID for character: {character}")

        character_id = character_id_res["id"]

        await self.insert_character_hit_points(character_id=character_id, hit_points=character.hit_points)
        await self.insert_character_classes(character_id=character_id, classes=character.classes)
        await self.insert_character_stat(character_id=character_id, character_stats=character.stats)
        for item in character.items:
            await self.insert_character_item(character_id=character_id, character_item=item)
        await self.insert_character_defenses(character_id=character_id, defenses=character.defenses)

    async def insert_character_hit_points(self, character_id: int, hit_points: CharacterHitpoints):
        LOG.info(f"Inserting character hitpoints for character id {character_id}")
        await self.db.execute(
            """
            INSERT INTO operational.character_hitpoints
            (character_id, hit_point_max, current_hit_points, temporary_hit_points)
            VALUES
            (%(character_id)s, %(hit_point_max)s, %(current_hit_points)s, %(temporary_hit_points)s)
            """,
            {"character_id": character_id} | msgspec.structs.asdict(hit_points),
        )

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

        item_id = item_id_res["id"]

        LOG.info(f"Inserting character item modifier for character item id {item_id}")
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
