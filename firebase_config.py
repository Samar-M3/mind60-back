import firebase_admin
from firebase_admin import credentials, firestore, auth
import os
from dotenv import load_dotenv

load_dotenv()

# Firebase initialization
def initialize_firebase():
    if not firebase_admin._apps:
        # Check if we have a service account key file
        service_account_path = os.getenv("FIREBASE_SERVICE_ACCOUNT_KEY_PATH")
        
        if service_account_path and os.path.exists(service_account_path):
            cred = credentials.Certificate(service_account_path)
            firebase_admin.initialize_app(cred)
        else:
            # If no service account key, we'll use default credentials
            # This works if you're running on Google Cloud or have GOOGLE_APPLICATION_CREDENTIALS set
            try:
                firebase_admin.initialize_app()
            except Exception as e:
                print(f"Warning: Could not initialize Firebase: {e}")
                print("Make sure GOOGLE_APPLICATION_CREDENTIALS env var is set or service account key is provided")

def get_db():
    """Get Firestore database instance"""
    return firestore.client()

def get_auth():
    """Get Firebase Auth instance"""
    return auth
