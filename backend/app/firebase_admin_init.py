import firebase_admin
from firebase_admin import credentials
from pathlib import Path

_initialized = False

def get_firebase_app():
    global _initialized
    if not _initialized:
        key_path = Path(__file__).resolve().parent.parent / "serviceAccountKey.json"
        cred = credentials.Certificate(str(key_path))
        firebase_admin.initialize_app(cred)
        _initialized = True
    return firebase_admin.get_app()
