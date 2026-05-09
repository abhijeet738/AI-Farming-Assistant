"""
Rate limiting configuration using slowapi.

Applies per-IP rate limits to all endpoints to prevent abuse
and control costs on external API calls (Gemini, OpenWeatherMap).
"""

from slowapi import Limiter
from slowapi.util import get_remote_address

# Limiter keyed by client IP address
limiter = Limiter(key_func=get_remote_address)
