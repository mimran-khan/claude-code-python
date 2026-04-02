"""Remote managed settings service. Migrated from: services/remoteManagedSettings/*.ts"""

from .service import (
    clear_remote_managed_settings_cache,
    compute_checksum_from_settings,
    fetch_and_load_remote_managed_settings,
    initialize_remote_managed_settings_loading_promise,
    is_eligible_for_remote_managed_settings,
    load_remote_managed_settings,
    refresh_remote_managed_settings,
    start_background_polling,
    stop_background_polling,
    wait_for_remote_managed_settings_to_load,
)
from .sync_cache import is_remote_managed_settings_eligible, reset_sync_cache
from .sync_cache_state import (
    get_remote_managed_settings_sync_from_cache,
    get_settings_path,
    set_session_cache,
)
from .sync_cache_state import (
    reset_sync_cache as reset_sync_cache_state,
)
from .types import RemoteManagedSettingsFetchResult, parse_remote_settings_response

__all__ = [
    "RemoteManagedSettingsFetchResult",
    "parse_remote_settings_response",
    "get_remote_managed_settings_sync_from_cache",
    "get_settings_path",
    "set_session_cache",
    "reset_sync_cache_state",
    "is_remote_managed_settings_eligible",
    "reset_sync_cache",
    "compute_checksum_from_settings",
    "is_eligible_for_remote_managed_settings",
    "initialize_remote_managed_settings_loading_promise",
    "wait_for_remote_managed_settings_to_load",
    "load_remote_managed_settings",
    "refresh_remote_managed_settings",
    "clear_remote_managed_settings_cache",
    "start_background_polling",
    "stop_background_polling",
    "fetch_and_load_remote_managed_settings",
]
