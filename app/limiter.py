"""
AlphaWatch AI — Central Rate Limiter
ASTRAQUANT X 2026

Configures SlowAPI Limiter with client IP address keying.
Centrally defined to prevent circular import dependencies between app/main.py
and route handlers.
"""

from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(
    key_func=get_remote_address,
    default_limits=["200/minute"],
)
