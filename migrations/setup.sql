CREATE SCHEMA IF NOT EXISTS operational;

CREATE TABLE IF NOT EXISTS operational.character (
    id SERIAL PRIMARY KEY,
    name TEXT NOT NULL,
    level INT NOT NULL DEFAULT 1,
    hit_points INT NOT NULL
);

CREATE TABLE IF NOT EXISTS operational.character_class (
    id SERIAL PRIMARY KEY,
    character_id INT REFERENCES operational.character(id),
    class_name TEXT NOT NULL,
    hit_dice_value INT NOT NULL,
    class_level INT NOT NULL DEFAULT 1
);

CREATE TABLE IF NOT EXISTS operational.character_stat (
    id SERIAL PRIMARY KEY,
    character_id INT REFERENCES operational.character(id),
    stat TEXT NOT NULL,
    value INT NOT NULL
);

CREATE TABLE IF NOT EXISTS operational.character_item (
    id SERIAL PRIMARY KEY,
    character_id INT REFERENCES operational.character(id),
    name TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS operational.character_item_modifier (
    id SERIAL PRIMARY KEY,
    character_item_id INT REFERENCES operational.character_item(id),
    affected_object TEXT NOT NULL,
    affected_value TEXT NOT NULL,
    value INT NOT NULL
);

CREATE TABLE IF NOT EXISTS operational.character_defense (
    id SERIAL PRIMARY KEY,
    character_id INT REFERENCES operational.character(id),
    damage_type TEXT NOT NULL,
    defense_type TEXT NOT NULL
);