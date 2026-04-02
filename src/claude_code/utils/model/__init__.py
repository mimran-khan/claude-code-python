"""
Model utilities.

Model selection, configuration, and management.

Migrated from: utils/model/*.ts
"""

from .aliases import (
    AVAILABLE_ALIASES,
    ModelAlias,
    is_model_alias,
    resolve_model_alias,
)
from .capabilities import (
    ModelCapabilities,
    get_model_capabilities,
    supports_thinking,
    supports_tool_use,
    supports_vision,
)
from .configs import (
    DEFAULT_MODEL_CONFIGS,
    ModelConfig,
    get_model_config,
)
from .model import (
    ModelName,
    ModelSetting,
    get_best_model,
    get_default_haiku_model,
    get_default_main_loop_model,
    get_default_main_loop_model_setting,
    get_default_opus_model,
    get_default_sonnet_model,
    get_main_loop_model,
    get_public_model_display_name,
    get_small_fast_model,
    get_user_specified_model_setting,
    is_legacy_model_remap_enabled,
    is_non_custom_opus_model,
    is_opus_1m_merge_enabled,
    parse_user_specified_model,
    render_model_name,
)
from .providers import (
    APIProvider,
    get_api_provider,
    is_bedrock,
    is_first_party,
    is_foundry,
    is_vertex,
)

__all__ = [
    # Model
    "ModelName",
    "ModelSetting",
    "get_default_main_loop_model",
    "get_default_main_loop_model_setting",
    "get_main_loop_model",
    "get_small_fast_model",
    "get_best_model",
    "get_default_opus_model",
    "get_default_sonnet_model",
    "get_default_haiku_model",
    "get_user_specified_model_setting",
    "get_public_model_display_name",
    "is_legacy_model_remap_enabled",
    "is_non_custom_opus_model",
    "is_opus_1m_merge_enabled",
    "parse_user_specified_model",
    "render_model_name",
    # Providers
    "APIProvider",
    "get_api_provider",
    "is_first_party",
    "is_bedrock",
    "is_vertex",
    "is_foundry",
    # Aliases
    "ModelAlias",
    "is_model_alias",
    "resolve_model_alias",
    "AVAILABLE_ALIASES",
    # Capabilities
    "ModelCapabilities",
    "get_model_capabilities",
    "supports_tool_use",
    "supports_vision",
    "supports_thinking",
    # Configs
    "ModelConfig",
    "get_model_config",
    "DEFAULT_MODEL_CONFIGS",
]
