"""
Client keys and lazy env-dependent lookups.

Migrated from: constants/keys.ts
"""

import os

from ..utils.env_utils import is_env_truthy


def get_growth_book_client_key() -> str:
    """
    GrowthBook SDK key; respects USER_TYPE and ENABLE_GROWTHBOOK_DEV.

    Lazy read so ENABLE_GROWTHBOOK_DEV applied after import is visible.
    """
    user_type = os.environ.get("USER_TYPE", "")
    if user_type == "ant":
        if is_env_truthy(os.environ.get("ENABLE_GROWTHBOOK_DEV")):
            return "sdk-yZQvlplybuXjYh6L"
        return "sdk-xRVcrliHIlrg4og4"
    return "sdk-zAZezfDKGoZuXXKe"
