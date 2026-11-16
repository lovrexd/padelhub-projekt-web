from typing import Any


def reject_null(value: Any) -> Any:
    """Sprječava postavljanje obaveznog polja na null pri djelomičnoj izmjeni (PATCH).

    Ako polje nije poslano u JSON-u, ovaj validator se ne poziva i zadrži se
    zadani None (koji exclude_unset=True preskače). Ako klijent izričito
    pošalje {"polje": null}, validator to odbija s 422.
    """
    if value is None:
        raise ValueError("Polje ne smije biti null")
    return value
