"""
Utility functions and constants.
"""

import re
from datetime import datetime
from mongoengine import errors
from uuid import uuid4


PASS_MIN_LEN = 8
# Accept any character, at least `PASS_MIN_LEN` long.
PASS_MIN_REGEX = r'.{{{min},}}$'.format(min=PASS_MIN_LEN)
EMAIL_REGEX = re.compile(
    r'\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,4}\b',
    re.IGNORECASE
)

PASSWORD_ERROR_MSG = 'Password must be at least {} characters long'.format(
    PASS_MIN_LEN
)


def utcnow():
    """
    Returns the current (naive) UTC datetime.
    """
    return datetime.utcnow()


def validate_password(password):
    """
    Validates a password.

    Fails if the password has less than `PASS_MIN_LEN` characters long.

    :param password: The password to validate.
    :return: ValidationError if the validation fails.
    """
    if not password or not re.match(PASS_MIN_REGEX, password):
        raise errors.ValidationError(
            errors={'password': PASSWORD_ERROR_MSG}
        )


def generate_random_password():
    """
    Generates a random password.
    """
    return uuid4().get_hex()