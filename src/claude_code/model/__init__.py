"""
Model Module.

Handles model configuration, selection, and provider management.
"""

from .cost import (
    calculate_cost_from_tokens,
    get_model_input_cost_per_token,
    get_model_output_cost_per_token,
)
from .models import (
    get_default_model,
    get_default_opus_model,
    get_default_sonnet_model,
    get_model_context_window,
    get_small_fast_model,
    is_haiku_model,
    is_opus_model,
    is_sonnet_model,
)
from .providers import (
    APIProvider,
    get_api_provider,
    is_first_party_base_url,
)

__all__ = [
    # Providers
    "APIProvider",
    "get_api_provider",
    "is_first_party_base_url",
    # Models
    "get_default_model",
    "get_default_sonnet_model",
    "get_default_opus_model",
    "get_small_fast_model",
    "is_opus_model",
    "is_sonnet_model",
    "is_haiku_model",
    "get_model_context_window",
    # Cost
    "get_model_input_cost_per_token",
    "get_model_output_cost_per_token",
    "calculate_cost_from_tokens",
]
