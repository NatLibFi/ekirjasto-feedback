"""Load municipality names and feedback recipients from Circulation."""

import logging
import os
import time

import httpx
from config import app

_CACHE_TTL_SECONDS = 86400
_STALE_RETRY_SECONDS = 60
_municipalities_cache = None
_cache_expires_at = 0.0


class MunicipalityRegistryUnavailable(RuntimeError):
    """Raised when no municipality registry is available."""


def _configuration(name):
    return os.environ.get(name) or app.config.get(name)


def _normalize_municipalities(rows):
    if not isinstance(rows, list):
        raise ValueError("Municipality registry response is invalid.")

    municipalities = []
    seen_codes = set()
    for row in rows:
        if not isinstance(row, dict):
            raise ValueError("Municipality registry response is invalid.")
        code = row.get("code")
        name = row.get("name")
        if not isinstance(code, str) or not isinstance(name, str):
            raise ValueError("Municipality registry response is invalid.")
        code = code.strip()
        name = name.strip()
        if not code or not name or code in seen_codes:
            raise ValueError("Municipality registry response is invalid.")
        seen_codes.add(code)
        email = row.get("email")
        if email is not None and not isinstance(email, str):
            raise ValueError("Municipality registry response is invalid.")
        municipalities.append(
            {
                "code": code,
                "name": name,
                "email": email.strip() or None if email is not None else None,
            }
        )
    if not municipalities:
        raise ValueError("Municipality registry response is empty.")
    return municipalities


def get_municipalities():
    """Return cached municipalities, refreshing them from Circulation as needed."""
    global _municipalities_cache, _cache_expires_at

    if _municipalities_cache is not None and time.monotonic() < _cache_expires_at:
        return _municipalities_cache

    url = _configuration("FEEDBACK_MUNICIPALITIES_URL")
    token = _configuration("FEEDBACK_SERVICE_TOKEN")
    if not url or not token:
        if _municipalities_cache is not None:
            logging.warning(
                "Municipality registry service is not configured; using cached data."
            )
            _cache_expires_at = time.monotonic() + _STALE_RETRY_SECONDS
            return _municipalities_cache
        logging.error(
            "Municipality registry service is not configured and no cached data is available."
        )
        raise MunicipalityRegistryUnavailable(
            "Municipality registry service is not configured."
        )

    try:
        response = httpx.get(
            url,
            headers={"Authorization": f"Bearer {token}"},
            timeout=5.0,
        )
        response.raise_for_status()
        payload = response.json()
        municipalities = _normalize_municipalities(payload["municipalities"])
    except (httpx.HTTPError, KeyError, TypeError, ValueError) as error:
        if _municipalities_cache is not None:
            logging.warning(
                "Could not refresh municipality registry; using cached data (%s).",
                type(error).__name__,
            )
            _cache_expires_at = time.monotonic() + _STALE_RETRY_SECONDS
            return _municipalities_cache
        logging.error(
            "Could not load municipality registry and no cached data is available (%s).",
            type(error).__name__,
        )
        raise MunicipalityRegistryUnavailable(
            "Could not load the municipality registry."
        ) from None

    _municipalities_cache = municipalities
    _cache_expires_at = time.monotonic() + _CACHE_TTL_SECONDS
    return _municipalities_cache


def indexed_municipalities():
    """Return form choices using municipality codes as stable values."""
    return [(item["code"], item["name"]) for item in get_municipalities()]


def municipality_for_code(code):
    """Return a municipality record by its stable Koodisto code."""
    return next(
        (item for item in get_municipalities() if item["code"] == str(code)),
        None,
    )


def index_to_email(code):
    municipality = municipality_for_code(code)
    return municipality["email"] if municipality else None


def index_to_name(code):
    municipality = municipality_for_code(code)
    if municipality is None:
        raise ValueError("Unknown municipality code.")
    return municipality["name"]
