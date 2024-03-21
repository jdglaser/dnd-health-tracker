from src.exceptions import AppError


class CharacterRepoException(AppError): ...


class CharacterNotFoundException(CharacterRepoException):
    def __init__(self, *args: object) -> None:
        super().__init__(*args)
