import firebase_admin
from firebase_admin import credentials, messaging
import os
from typing import List, Optional
import logging

logger = logging.getLogger(__name__)

class FirebaseService:
    _instance = None
    _initialized = False
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        if not self._initialized:
            try:
                cred_path = os.getenv("FIREBASE_CREDENTIALS_PATH")
                if not cred_path or not os.path.exists(cred_path):
                    logger.warning("Firebase credentials not found. Push notifications disabled.")
                    return
                
                cred = credentials.Certificate(cred_path)
                firebase_admin.initialize_app(cred)
                self._initialized = True
                logger.info("✅ Firebase initialized successfully")
            except Exception as e:
                logger.error(f"❌ Firebase initialization failed: {e}")
    
    def send_push_notification(
        self, 
        device_token: str, 
        title: str, 
        body: str,
        data: Optional[dict] = None
    ) -> bool:
        """Send push notification to a single device"""
        if not self._initialized:
            logger.warning("Firebase not initialized. Skipping push notification.")
            return False
        
        try:
            message = messaging.Message(
                notification=messaging.Notification(
                    title=title,
                    body=body
                ),
                data=data or {},
                token=device_token
            )
            
            response = messaging.send(message)
            logger.info(f"✅ Push notification sent: {response}")
            return True
        except Exception as e:
            logger.error(f"❌ Failed to send push notification: {e}")
            return False
    
    def send_multicast(
        self,
        device_tokens: List[str],
        title: str,
        body: str,
        data: Optional[dict] = None
    ) -> int:
        """Send push notification to multiple devices"""
        if not self._initialized:
            logger.warning("Firebase not initialized. Skipping push notification.")
            return 0
        
        try:
            message = messaging.MulticastMessage(
                notification=messaging.Notification(
                    title=title,
                    body=body
                ),
                data=data or {},
                tokens=device_tokens
            )
            
            response = messaging.send_multicast(message)
            logger.info(f"✅ Sent {response.success_count}/{len(device_tokens)} notifications")
            return response.success_count
        except Exception as e:
            logger.error(f"❌ Failed to send multicast notification: {e}")
            return 0

firebase_service = FirebaseService()
