from abc import ABC, abstractmethod


class SMSClientInterface(ABC):

    @abstractmethod
    def authenticate(self):
        """Method to authenticate the client and return a token."""
        pass

    @abstractmethod
    def send_sms(self, phone_number: str, message: str):
        """Method to send an SMS message to a given phone number."""
        pass
