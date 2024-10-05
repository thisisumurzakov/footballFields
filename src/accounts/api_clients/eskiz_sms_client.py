import os

import redis
import requests
from django.conf import settings

from .sms_client_interface import SMSClientInterface


class EskizSmsClient(SMSClientInterface):
    def __init__(self):
        self.base_url = "https://notify.eskiz.uz/api"
        self.email = os.getenv("ESKIZ_EMAIL")
        self.password = os.getenv("ESKIZ_PASSWORD")
        self.redis_client = redis.StrictRedis(
            host=settings.REDIS_HOST,
            port=settings.REDIS_PORT,
            db=settings.REDIS_DB,
            decode_responses=True,
        )

    def authenticate(self):
        token = self.redis_client.get("eskiz_token")
        if token:
            return token, None
        auth_url = f"{self.base_url}/auth/login"
        data = {"email": self.email, "password": self.password}
        response = requests.post(auth_url, data=data)
        if response.status_code == 200:
            token = response.json()["data"]["token"]
            self.redis_client.set("eskiz_token", token, ex=86390)
            return token, None
        else:
            error_message = "Authentication Failed: " + response.json().get(
                "message", "No error message provided"
            )
            return None, error_message

    def send_sms(self, phone_number, message):
        token, error = self.authenticate()
        if error:
            return False, error
        send_url = f"{self.base_url}/message/sms/send"
        headers = {"Authorization": f"Bearer {token}"}
        payload = {
            "mobile_phone": phone_number,
            "message": message,
            # 'from': '4546',  # Uncomment and use your registered sender name
        }
        response = requests.post(send_url, headers=headers, data=payload)
        if response.status_code == 200:
            return True, "SMS sent successfully"
        else:
            return False, f"Failed to send SMS with status code {response.status_code}"
