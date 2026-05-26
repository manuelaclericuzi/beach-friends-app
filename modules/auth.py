import hashlib

DEFAULT_ADMIN_PASSWORD = "admin123"


def hash_pin(pin: str) -> str:
    return hashlib.sha256(pin.strip().encode("utf-8")).hexdigest()


def verify(pin: str, stored_hash: str) -> bool:
    if not stored_hash:
        return False
    return hash_pin(pin) == stored_hash


def default_admin_hash() -> str:
    return hash_pin(DEFAULT_ADMIN_PASSWORD)
