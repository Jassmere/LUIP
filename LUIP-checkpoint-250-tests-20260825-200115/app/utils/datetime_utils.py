"""
LUIP DateTime Utilities

Centralised UTC datetime handling for LUIP.

LUIP database DateTime columns currently use naive UTC
timestamps. This helper provides the current UTC time
without using the deprecated datetime.utcnow().
"""

from datetime import datetime, UTC


def utcnow():
    """
    Return the current UTC time as a naive datetime.

    This preserves LUIP's existing database convention
    while avoiding the deprecated datetime.utcnow().
    """

    return datetime.now(UTC).replace(tzinfo=None)