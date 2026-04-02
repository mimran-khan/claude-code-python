"""
/bridge-kick — inject bridge failure states (ant-only).

Migrated from: commands/bridge-kick.ts
"""

from __future__ import annotations

import os

from claude_code.commands.protocols import get_bridge_debug_handle
from claude_code.commands.spec import CommandSpec

USAGE = """/bridge-kick <subcommand>
  close <code>              fire ws_closed with the given code (e.g. 1002)
  poll <status> [type]      next poll throws BridgeFatalError(status, type)
  poll transient            next poll throws axios-style rejection (5xx/net)
  register fail [N]         next N registers transient-fail (default 1)
  register fatal            next register 403s (terminal)
  reconnect-session fail    next POST /bridge/reconnect fails
  heartbeat <status>        next heartbeat throws BridgeFatalError(status)
  reconnect                 call reconnectEnvironmentWithSession directly
  status                    print bridge state"""


async def bridge_kick_call(args: str) -> dict[str, str]:
    """Return LocalCommandResult-shaped dict."""
    h = get_bridge_debug_handle()
    if h is None:
        return {
            "type": "text",
            "value": ("No bridge debug handle registered. Remote Control must be connected (USER_TYPE=ant)."),
        }

    parts = args.strip().split()
    sub = parts[0] if parts else ""
    a = parts[1] if len(parts) > 1 else None
    b = parts[2] if len(parts) > 2 else None

    if sub == "close":
        if a is None:
            return {"type": "text", "value": f"close: need a numeric code\n{USAGE}"}
        try:
            code_i = int(a)
        except ValueError:
            return {"type": "text", "value": f"close: need a numeric code\n{USAGE}"}
        h.fire_close(code_i)
        return {
            "type": "text",
            "value": (f"Fired transport close({code_i}). Watch debug.log for [bridge:repl] recovery."),
        }

    if sub == "poll":
        if a == "transient":
            h.inject_fault(
                {
                    "method": "pollForWork",
                    "kind": "transient",
                    "status": 503,
                    "count": 1,
                }
            )
            h.wake_poll_loop()
            return {
                "type": "text",
                "value": ("Next poll will throw a transient (axios rejection). Poll loop woken."),
            }
        if a is None:
            return {
                "type": "text",
                "value": f"poll: need 'transient' or a status code\n{USAGE}",
            }
        try:
            st = int(a)
        except ValueError:
            return {
                "type": "text",
                "value": f"poll: need 'transient' or a status code\n{USAGE}",
            }
        error_type = b or ("not_found_error" if st == 404 else "authentication_error")
        h.inject_fault(
            {
                "method": "pollForWork",
                "kind": "fatal",
                "status": st,
                "errorType": error_type,
                "count": 1,
            }
        )
        h.wake_poll_loop()
        return {
            "type": "text",
            "value": (f"Next poll will throw BridgeFatalError({st}, {error_type}). Poll loop woken."),
        }

    if sub == "register":
        if a == "fatal":
            h.inject_fault(
                {
                    "method": "registerBridgeEnvironment",
                    "kind": "fatal",
                    "status": 403,
                    "errorType": "permission_error",
                    "count": 1,
                }
            )
            return {
                "type": "text",
                "value": ("Next registerBridgeEnvironment will 403. Trigger with close/reconnect."),
            }
        n = int(b) if b and b.isdigit() else 1
        h.inject_fault(
            {
                "method": "registerBridgeEnvironment",
                "kind": "transient",
                "status": 503,
                "count": n,
            }
        )
        return {
            "type": "text",
            "value": (f"Next {n} registerBridgeEnvironment call(s) will transient-fail. Trigger with close/reconnect."),
        }

    if sub == "reconnect-session":
        h.inject_fault(
            {
                "method": "reconnectSession",
                "kind": "fatal",
                "status": 404,
                "errorType": "not_found_error",
                "count": 2,
            }
        )
        return {
            "type": "text",
            "value": (
                "Next 2 POST /bridge/reconnect calls will 404. doReconnect Strategy 1 falls through to Strategy 2."
            ),
        }

    if sub == "heartbeat":
        status = int(a) if a and a.isdigit() else 401
        h.inject_fault(
            {
                "method": "heartbeatWork",
                "kind": "fatal",
                "status": status,
                "errorType": ("authentication_error" if status == 401 else "not_found_error"),
                "count": 1,
            }
        )
        return {
            "type": "text",
            "value": (f"Next heartbeat will {status}. Watch for onHeartbeatFatal → work-state teardown."),
        }

    if sub == "reconnect":
        h.force_reconnect()
        return {
            "type": "text",
            "value": "Called reconnectEnvironmentWithSession(). Watch debug.log.",
        }

    if sub == "status":
        return {"type": "text", "value": h.describe()}

    return {"type": "text", "value": USAGE}


def _is_ant() -> bool:
    return os.environ.get("USER_TYPE") == "ant"


BRIDGE_KICK_SPEC = CommandSpec(
    type="local",
    name="bridge-kick",
    description="Inject bridge failure states for manual recovery testing",
    supports_non_interactive=False,
    is_enabled=_is_ant,
)

__all__ = ["BRIDGE_KICK_SPEC", "USAGE", "bridge_kick_call"]
