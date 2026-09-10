import json
import os
import threading

from config import DB_FILE, SUDO_USERS, OWNER_ID

_lock = threading.Lock()

_DEFAULT = {
    "sudo_users": list(set(SUDO_USERS + [OWNER_ID])),
    "authorized_chats": [],   # groups where non-sudo members may control playback
    "clones": {},             # {name: {"bot_token": ..., "added_by": user_id}}
}


def _load():
    if not os.path.exists(DB_FILE):
        _save(_DEFAULT)
        return dict(_DEFAULT)
    with open(DB_FILE, "r") as f:
        return json.load(f)


def _save(data):
    with open(DB_FILE, "w") as f:
        json.dump(data, f, indent=2)


def get_db():
    with _lock:
        return _load()


def is_sudo(user_id: int) -> bool:
    data = get_db()
    return user_id in data["sudo_users"]


def add_sudo(user_id: int):
    with _lock:
        data = _load()
        if user_id not in data["sudo_users"]:
            data["sudo_users"].append(user_id)
            _save(data)


def remove_sudo(user_id: int):
    with _lock:
        data = _load()
        if user_id in data["sudo_users"] and user_id != OWNER_ID:
            data["sudo_users"].remove(user_id)
            _save(data)


def authorize_chat(chat_id: int):
    with _lock:
        data = _load()
        if chat_id not in data["authorized_chats"]:
            data["authorized_chats"].append(chat_id)
            _save(data)


def unauthorize_chat(chat_id: int):
    with _lock:
        data = _load()
        if chat_id in data["authorized_chats"]:
            data["authorized_chats"].remove(chat_id)
            _save(data)


def is_authorized_chat(chat_id: int) -> bool:
    return chat_id in get_db()["authorized_chats"]


def add_clone(name: str, bot_token: str, added_by: int):
    with _lock:
        data = _load()
        data["clones"][name] = {"bot_token": bot_token, "added_by": added_by}
        _save(data)


def remove_clone(name: str):
    with _lock:
        data = _load()
        data["clones"].pop(name, None)
        _save(data)


def list_clones():
    return get_db()["clones"]
