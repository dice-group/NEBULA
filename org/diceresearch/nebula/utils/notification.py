from firebase_admin import messaging
import firebase_admin
from firebase_admin import credentials


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
        # Initialize Firebase
        cred = credentials.Certificate('/Users/nehapokharel/Documents/Nebula/nebula-a7726-firebase-adminsdk-432e4-764225c245.json')
        firebase_admin.initialize_app(cred)

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
        print('Message sent successfully:', response)
        return True
    except Exception as e:
        print('Error sending message:', str(e))
        return False



