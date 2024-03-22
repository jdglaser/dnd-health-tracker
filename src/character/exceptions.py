from src.common.app_error import AppError


class CharacterRepoException(AppError): ...


class CharacterNotFoundException(CharacterRepoException):
    def __init__(self, *args: object, character_id: int) -> None:
        self.character_id = character_id
        super().__init__(*args)
