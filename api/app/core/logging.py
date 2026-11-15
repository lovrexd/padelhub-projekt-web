import logging


def setup_logging(debug: bool = False) -> None:
    """Postavlja osnovno zapisivanje događaja (logova) poslužitelja."""
    logging.basicConfig(
        level=logging.DEBUG if debug else logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )
