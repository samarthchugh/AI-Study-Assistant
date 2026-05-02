import base64
import json
import firebase_admin
from firebase_admin import credentials
from app.config import settings

_initialized = False

def get_firebase_app():
    global _initialized
    if not _initialized:
        service_account_info = json.loads(base64.b64decode(settings.FIREBASE_SERVICE_ACCOUNT_B64).decode("utf-8"))
        cred = credentials.Certificate(service_account_info)
        firebase_admin.initialize_app(cred)
        _initialized = True
    return firebase_admin.get_app()
