import pytest
from litestar.status_codes import HTTP_200_OK, HTTP_404_NOT_FOUND
from litestar.testing import TestClient

from src.character.models import DamageType
from src.main import app


@pytest.fixture
def test_client():
    with TestClient(app=app, base_url="http://testserver.local/api/v1/") as client:
        yield client


def test_get_character(test_client: TestClient):
    response = test_client.get("character/1")
    assert response.status_code == HTTP_200_OK
    assert response.json() == {
        "name": "Briv",
        "level": 5,
        "hitPoints": {"hitPointMax": 25, "currentHitPoints": 25, "temporaryHitPoints": None},
        "classes": [{"name": "fighter", "hitDiceValue": 10, "classLevel": 5}],
        "stats": {"strength": 15, "dexterity": 12, "constitution": 14, "intelligence": 13, "wisdom": 10, "charisma": 8},
        "items": [
            {
                "name": "Ioun Stone of Fortitude",
                "modifier": {"affectedObject": "stats", "affectedValue": "constitution", "value": 2},
            }
        ],
        "defenses": [{"type": "fire", "defense": "immunity"}, {"type": "slashing", "defense": "resistance"}],
    }


def test_get_missing_character(test_client: TestClient):
    response = test_client.get("character/2")
    assert response.status_code == HTTP_404_NOT_FOUND
    assert response.json() == {"statusCode": 404, "detail": "Character id 2 not found", "extra": {}}


def test_damage_character(test_client: TestClient):
    response = test_client.put("character/1/hit-points/damage", json={"amount": 5, "damageType": DamageType.PIERCING})
    assert response.status_code == HTTP_200_OK
    assert response.json() == {
        "name": "Briv",
        "level": 5,
        "hitPoints": {"hitPointMax": 25, "currentHitPoints": 20, "temporaryHitPoints": None},
        "classes": [{"name": "fighter", "hitDiceValue": 10, "classLevel": 5}],
        "stats": {"strength": 15, "dexterity": 12, "constitution": 14, "intelligence": 13, "wisdom": 10, "charisma": 8},
        "items": [
            {
                "name": "Ioun Stone of Fortitude",
                "modifier": {"affectedObject": "stats", "affectedValue": "constitution", "value": 2},
            }
        ],
        "defenses": [{"type": "fire", "defense": "immunity"}, {"type": "slashing", "defense": "resistance"}],
    }


def test_heal_character(test_client: TestClient):
    response = test_client.put("character/1/hit-points/heal", json={"amount": 3})
    assert response.status_code == HTTP_200_OK
    assert response.json() == {
        "name": "Briv",
        "level": 5,
        "hitPoints": {"hitPointMax": 25, "currentHitPoints": 25, "temporaryHitPoints": None},
        "classes": [{"name": "fighter", "hitDiceValue": 10, "classLevel": 5}],
        "stats": {"strength": 15, "dexterity": 12, "constitution": 14, "intelligence": 13, "wisdom": 10, "charisma": 8},
        "items": [
            {
                "name": "Ioun Stone of Fortitude",
                "modifier": {"affectedObject": "stats", "affectedValue": "constitution", "value": 2},
            }
        ],
        "defenses": [{"type": "fire", "defense": "immunity"}, {"type": "slashing", "defense": "resistance"}],
    }


def test_assign_temporary_hit_points(test_client: TestClient):
    response = test_client.put("character/1/hit-points/temporary", json={"amount": 4})
    assert response.status_code == HTTP_200_OK
    assert response.json() == {
        "name": "Briv",
        "level": 5,
        "hitPoints": {"hitPointMax": 25, "currentHitPoints": 25, "temporaryHitPoints": 4},
        "classes": [{"name": "fighter", "hitDiceValue": 10, "classLevel": 5}],
        "stats": {"strength": 15, "dexterity": 12, "constitution": 14, "intelligence": 13, "wisdom": 10, "charisma": 8},
        "items": [
            {
                "name": "Ioun Stone of Fortitude",
                "modifier": {"affectedObject": "stats", "affectedValue": "constitution", "value": 2},
            }
        ],
        "defenses": [{"type": "fire", "defense": "immunity"}, {"type": "slashing", "defense": "resistance"}],
    }
