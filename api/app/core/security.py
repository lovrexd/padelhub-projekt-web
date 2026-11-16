import bcrypt


def hash_password(plain: str) -> str:
    """Pretvara čistu lozinku u sigurni bcrypt hash s nasumičnim saltom."""
    return bcrypt.hashpw(plain.encode(), bcrypt.gensalt()).decode()


def verify_password(plain: str, hashed: str) -> bool:
    """Uspoređuje unesenu lozinku sa spremljenim bcrypt hashom u stalnom vremenu."""
    return bcrypt.checkpw(plain.encode(), hashed.encode())
