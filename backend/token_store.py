_store: dict[str, bytes] = {}


def save_token(user_id: str, encrypted_token: bytes) -> None:
    _store[user_id] = encrypted_token


def get_token(user_id: str) -> bytes | None:
    return _store.get(user_id)


def delete_token(user_id: str) -> None:
    _store.pop(user_id, None)
