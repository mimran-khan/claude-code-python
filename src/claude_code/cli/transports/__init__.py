"""
CLI transports: WebSocket, SSE, hybrid POST, CCR client helpers.

Migrated from: cli/transports/*.ts
"""

from .ccr_client import (
    CCRClient,
    CCRInitError,
    InternalEvent,
    StreamAccumulatorState,
    accumulate_stream_events,
    clear_stream_accumulator_for_message,
    create_stream_accumulator,
    decode_jwt_expiry,
)
from .hybrid_transport import HybridTransport
from .serial_batch_event_uploader import RetryableError, SerialBatchEventUploader
from .sse_transport import SSETransport, StreamClientEvent, parse_sse_frames
from .transport_base import StdoutMessage, Transport
from .transport_utils import get_transport_for_url
from .websocket_transport import WebSocketTransport, WebSocketTransportOptions
from .worker_state_uploader import WorkerStateUploader, coalesce_patches

__all__ = [
    "StdoutMessage",
    "Transport",
    "RetryableError",
    "SerialBatchEventUploader",
    "WorkerStateUploader",
    "coalesce_patches",
    "SSETransport",
    "StreamClientEvent",
    "parse_sse_frames",
    "WebSocketTransport",
    "WebSocketTransportOptions",
    "HybridTransport",
    "get_transport_for_url",
    "CCRClient",
    "CCRInitError",
    "InternalEvent",
    "StreamAccumulatorState",
    "accumulate_stream_events",
    "clear_stream_accumulator_for_message",
    "create_stream_accumulator",
    "decode_jwt_expiry",
]
