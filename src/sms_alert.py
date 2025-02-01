import urllib.parse

import requests


class SMSAPIError(Exception):
    """Base class for SMS API-related errors."""

    pass


class MissingParameter(SMSAPIError):
    """HTTP error 400: Mandatory parameter is missing."""

    pass


class TooManySMS(SMSAPIError):
    """HTTP error 402: Too many SMSs have been sent too quickly."""

    pass


class ServiceNotEnabled(SMSAPIError):
    """HTTP error 403: Service not activated, or incorrect login/key."""

    pass


class ServerError(SMSAPIError):
    """HTTP error 500: Server error, please try again later."""

    pass


class SMSAPI:
    """SMS API client for sending SMS messages."""

    BASE_URL = "https://smsapi.free-mobile.fr/sendmsg"

    def __init__(self, user: str, password: str) -> None:
        """
        Initializes the SMSAPI client.

        Args:
            user (str): The user identifier.
            password (str): The password associated with the user account.
        """
        self.user: str = user
        self.password: str = password

    def send_sms(self, msg: str) -> None:
        """
        Sends a message via the SMS API using GET method.

        Args:
            msg (str): The message to be sent.

        Raises:
            MissingParameter: If a required parameter is missing.
            TooManySMS: If too many SMS messages have been sent quickly.
            ServiceNotEnabled: If the SMS service is not enabled or login/key is incorrect.
            ServerError: If there is an issue with the server.
        """
        # URL encode the message
        encoded_msg: str = urllib.parse.quote(msg)

        # Construct the URL with query parameters
        url: str = (
            f"{self.BASE_URL}?user={self.user}&pass={self.password}&msg={encoded_msg}"
        )

        # Send the GET request
        response: requests.Response = requests.get(url)

        # Handle the response
        self._handle_response(response)

    @staticmethod
    def _handle_response(response: requests.Response) -> None:
        """
        Handles the HTTP response, raising appropriate exceptions for errors.

        Args:
            response (requests.Response): The HTTP response from the SMS API.

        Raises:
            MissingParameter: For HTTP 400 error.
            TooManySMS: For HTTP 402 error.
            ServiceNotEnabled: For HTTP 403 error.
            ServerError: For HTTP 500 error.
        """
        error_map: dict[int, SMSAPIError] = {
            400: MissingParameter(
                "One of the mandatory parameters is missing."
            ),
            402: TooManySMS("Too many SMS messages sent in a short time."),
            403: ServiceNotEnabled(
                "Service not activated, or incorrect login/key."
            ),
            500: ServerError("Server error, please try again later."),
        }

        if response.status_code == 200:
            print("SMS sent successfully.")
        elif response.status_code in error_map:
            raise error_map[response.status_code]
        else:
            response.raise_for_status()
