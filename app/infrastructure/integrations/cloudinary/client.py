# app/infrastructure/cloudinary/client.py
from __future__ import annotations

import cloudinary

from app.core.config import get_settings

_configured = False


def configure_cloudinary() -> None:
    """
    Configure Cloudinary once per process.
    Safe to call multiple times.
    """
    global _configured
    if _configured:
        return

    s = get_settings()
    cloudinary.config(
        cloud_name=s.cloudinary_cloud_name,
        api_key=s.cloudinary_api_key,
        api_secret=s.cloudinary_api_secret,
        secure=True,  # always use https URLs
    )
    _configured = True
