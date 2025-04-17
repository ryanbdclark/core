"""Constants used for Owlet tests."""

AUTH_RETURN = {
    "api_token": "123456789",
    "expiry": 99999999999,
    "refresh": "ABCDEFGHIJ",
}

REAUTH_RETURN = {
    "api_token": "ABCDEFGHIJ",
    "expiry": 99999999999,
    "refresh": "123456789",
}


CONF_INPUT = {
    "region": "europe",
    "email": "owlet_email@email.com",
    "password": "owlet_password",
}


"""Common methods and const used across tests for Owlet."""
REGION = "europe"
EMAIL = "owlet_email@email.com"
PASSWORD = "owlet_password"
API_KEY = "123456789"
REFRESH = "ABCDEFGHIJ"
EXPIRY = 99999999999
EXPIRY_OLD = 1
