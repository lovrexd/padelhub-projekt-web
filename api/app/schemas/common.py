from typing import Any

MAX_INT32 = 2_147_483_647


def reject_null(value: Any) -> Any:
    if value is None:
        raise ValueError("Polje ne smije biti null")
    return value


def reject_nul_char(value: str) -> str:
    if "\x00" in value:
        raise ValueError("Tekst ne smije sadržavati NUL znak")
    return value
