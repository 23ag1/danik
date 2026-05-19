import hashlib


def hash_author(user_id: str) -> str:
    return hashlib.sha256(user_id.encode()).hexdigest()
