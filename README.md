# D&D Health Tracker API

[![Test, Lint, and Type Check](https://github.com/jdglaser/dnd-health-tracker/actions/workflows/validate.yml/badge.svg)](https://github.com/jdglaser/dnd-health-tracker/actions/workflows/validate.yml)

A health tracker REST API for D&D.

Allows clients to:
+ **Deal Damage** of a specific damage type taking into account damage resistance and immunity as well as temporary hit points
+ **Heal Hit Points**
+ **Add Temporary Hit Points**

## Tools, Libraries, and Frameworks

|   |   |
|---|---|
|**Language**|[Python 3.12](https://www.python.org/downloads/release/python-3122/)|
|**Web Framework**|[Litestar](https://litestar.dev/)|
|**Database**|[Postgres](https://www.postgresql.org/)|
|**Containerization**|[Docker](https://www.docker.com/)|
|**Testing**|[pytest](https://docs.pytest.org/en/8.0.x/)|
|**Type Checking**|[pyright](https://github.com/microsoft/pyright)|
|**Linting**|[Flake8](https://flake8.pycqa.org/en/latest/)|
|**CI/CD**|[GitHub Actions](https://github.com/features/actions)|

## Running the API Locally

### With Docker

1. Install [Docker](https://www.docker.com/) if you haven't already
2. Clone and open this repo locally
3. Run `docker compose up`

### With Python

1. Install [Python 3.12](https://www.python.org/downloads/release/python-3122/) if you haven't already
2. Install [Docker](https://www.docker.com/) if you haven't already
3. Clone and open this repo locally
4. Create a virtualenv by running `python3.12 -m venv .venv`
5. Activate the virtualenv with `source ./.venv/bin/activate`
6. Install requirements with `pip install -r requirements_dev.txt`
7. Startup the local Postgres database with `docker compose up db -d`
8. Start the API server by running `python -m src.main`

## Interacting with the API locally

Once you have the API running locally with one of the [methods mentioned above](#running-the-api-locally), you can
+ view the OpenAPI docs at http://localhost:3000/api/v1/docs
+ view the interactive swagger docs at http://localhost:3000/api/v1/docs/swagger

### Local test data

If the app is running in a [local environment](https://github.com/jdglaser/dnd-health-tracker/blob/main/src/common/app_config.py#L9), every time the app starts up it runs DDL and loads the [briv.json](briv.json) data into the database using the [migrations/setup.sql](migrations/setup.sql) script and the methods in the [src/character/character_controller.py](src/character/character_controller.py) class. Additionally, whenever the app shuts down, the database will be torn down using the [migrations/teardown.sql](migrations/teardown.sql) script.

Normally, in a real app, we'd use a database migration tool like [Flyway](https://flywaydb.org/) to handle migrations.

## Test Coverage

Unit and integration tests are primarily focused on the `character/hit-points` endpoints.
+ Unit tests for database methods can be found in [tests/test_character_repo.py](tests/test_character_repo.py)
+ Unit tests for service methods can be found in [tests/test_character_service.py](tests/test_character_service.py)
+ Integration tests for controller methods can be found in [tests/test_character_controller.py](tests/test_character_controller.py)

### Running Tests Locally

1. Follow the setup steps 1-7 in the [Running the API Locally / With Python section](#with-python) above.
2. Close any locally running instances of the app to avoid conflicts with the database (in a real app I would probably spin up a separate unit test database with docker to avoid this issue)
3. Run `python -m pytest tests`

## GitHub Actions

A few basic CI/CD steps exist for this project in GitHub actions. The definition of the actions can be found in [.github/workflows/validate.yml](.github/workflows/validate.yml).

On every push to a branch and all pull requests, the following jobs will run:
+ `unit-tests` - spins up the test postgres database and runs the full test suite
+ `lint` - Runs linting on the codebase using [flake8](https://flake8.pycqa.org/en/latest/)
+ `type-check` - Runs static type checking on the codebase using [pyright](https://github.com/microsoft/pyright)

You can view the latest run of the CI/CD pipeline here:
[![Test, Lint, and Type Check](https://github.com/jdglaser/dnd-health-tracker/actions/workflows/validate.yml/badge.svg)](https://github.com/jdglaser/dnd-health-tracker/actions/workflows/validate.yml)

## Logging

If the [environment](https://github.com/jdglaser/dnd-health-tracker/blob/main/src/common/app_config.py#L8) is anything other than `LOCAL_DEV`, then application logs will use the custom `StructuredFormatter` class to output logs as JSON objects for better parsing by logging monitoring tools. Otherwise, logs will use the `ColorFormatter` class for more human-readable logs.

## Contact

For more information or questions, please reach out to [Jarred Glaser](mailto:jarred.glaser@gmail.com).