"""
Firebase Admin SDK bootstrap utilities.
"""

import os
import firebase_admin
from firebase_admin import auth, credentials, firestore

from backend.core.config import settings


def init_firebase():
    """
    Initialize the Firebase admin app if it hasn't been initialised yet.
    Returns the firebase app instance for reuse.
    """
    if firebase_admin._apps:
        return firebase_admin.get_app()

    cred_path = settings.firebase_credentials_path or os.getenv(
        "FIREBASE_CREDENTIALS_PATH"
    )

    if cred_path and os.path.exists(cred_path):
        cred = credentials.Certificate(cred_path)
        firebase_admin.initialize_app(cred)
    else:
        # Default credentials will be used if running in a GCP environment
        firebase_admin.initialize_app()

    return firebase_admin.get_app()


def get_db():
    """Return a Firestore client (ensures Firebase is initialised)."""
    init_firebase()
    return firestore.client()


def verify_id_token(token: str):
    """Verify and decode a Firebase ID token."""
    init_firebase()
    return auth.verify_id_token(token)


def get_auth():
    """Return Firebase auth module for convenience."""
    init_firebase()
    return auth

