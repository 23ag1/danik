import hashlib


def hash_author(user_id: str) -> str:
    return hashlib.sha256(user_id.encode()).hexdigest()


def hash_item(feed_url: str, uid: str) -> str:
    return hashlib.sha256(f"{feed_url}::{uid}".encode()).hexdigest()
