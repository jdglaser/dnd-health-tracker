import hashlib
from enum import Enum
from typing import Any, NoReturn, Optional, Sequence

from psycopg import AsyncCursor, InterfaceError
from psycopg.cursor import BaseCursor
from psycopg.pq.abc import PGresult
from psycopg.rows import COMMAND_OK, SINGLE_TUPLE, TUPLES_OK, DictRow, RowMaker

from src.common.log_config import get_logger

LOG = get_logger(__name__)


class CaseInsensitiveEnum(Enum):
    @classmethod
    def _missing_(cls, value: object):
        for member in cls:
            if member.name.lower() == str(value).lower():
                return member


async def acquire_lock(key: str, cur: AsyncCursor):
    key_bytes: bytes = key.encode("utf-8")
    m = hashlib.sha256()
    m.update(key_bytes)
    key_int = int.from_bytes(m.digest()[:8], byteorder="big", signed=True)
    LOG.info(f"Attempting to retrieve lock {key} ({key_int})")
    await cur.execute("SELECT pg_advisory_xact_lock(%(hash)s)", {"hash": key_int})
    LOG.info(f"Successfully retrieved lock {key} ({key_int})")


def snake_to_camel(string: str):
    string_split = string.split("_")
    if len(string_split) == 1:
        return string
    return f"{string_split[0]}{''.join(s.capitalize() for s in string_split[1:])}"


def no_result(values: Sequence[Any]) -> NoReturn:
    """
    A `RowMaker` that always fail.

    It can be used as return value for a `RowFactory` called with no result.
    Note that the `!RowFactory` *will* be called with no result, but the
    resulting `!RowMaker` never should.
    """
    raise InterfaceError("the cursor doesn't have a result")


def _get_nfields(res: PGresult) -> Optional[int]:
    """
    Return the number of columns in a result, if it returns tuples else None

    Take into account the special case of results with zero columns.
    """
    nfields = res.nfields

    if (
        res.status == TUPLES_OK
        or res.status == SINGLE_TUPLE
        # "describe" in named cursors
        or (res.status == COMMAND_OK and nfields)
    ):
        return nfields
    else:
        return None


def _get_names_camel(cursor: BaseCursor) -> Optional[list[str]]:
    res = cursor.pgresult
    if not res:
        return None

    nfields = _get_nfields(res)
    if nfields is None:
        return None

    enc = cursor._encoding  # type: ignore [reportPrivateUsage]
    return [snake_to_camel(res.fname(i).decode(enc)) for i in range(nfields)]  # type: ignore[union-attr]


def dict_row_camel(cursor: BaseCursor) -> RowMaker[DictRow]:
    """
    Row factory to represent rows as dictionaries with all keys converted from snake case to camel case.

    The dictionary keys are taken from the column names of the returned columns.
    """
    names = _get_names_camel(cursor)
    if names is None:
        return no_result

    def dict_row_(values: Sequence[Any]) -> dict[str, Any]:
        return dict(zip(names, values))

    return dict_row_
