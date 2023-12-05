import logging

import firebase_admin
from firebase_admin import credentials, messaging


# Initialize Firebase
import settings

cred = credentials.Certificate(settings.firebase_certificate)
firebase_admin.initialize_app(cred)

def send_firebase_notification(registration_token, title, body):
    """
    Send a Firebase Cloud Messaging (FCM) notification to a specific device.

    Args:
        registration_token (str): The device's registration token.
        title (str): The title of the notification.
        body (str): The body of the notification.

    Returns:
        bool: True if the notification was sent successfully, False otherwise.
    """
    try:
        # Compose the notification message
        message = messaging.Message(
            notification=messaging.Notification(
                title=title,
                body=body
            ),
            token=registration_token
        )

        # Send the message
        response = messaging.send(message)
        logging.info('Message sent successfully:', response)
        return True
    except Exception as e:
        logging.error('Error sending message:', str(e))
        return False



