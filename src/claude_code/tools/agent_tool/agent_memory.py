"""
Agent memory management.

Memory and state persistence for agents.

Migrated from: tools/AgentTool/agentMemory.ts + agentMemorySnapshot.ts
"""

from __future__ import annotations

import json
import os
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any


@dataclass
class AgentMemoryEntry:
    """A single memory entry for an agent."""

    key: str
    value: Any
    timestamp: float = field(default_factory=lambda: datetime.now().timestamp())
    source: str = "agent"

    def to_dict(self) -> dict[str, Any]:
        return {
            "key": self.key,
            "value": self.value,
            "timestamp": self.timestamp,
            "source": self.source,
        }

    @staticmethod
    def from_dict(data: dict[str, Any]) -> AgentMemoryEntry:
        return AgentMemoryEntry(
            key=data["key"],
            value=data["value"],
            timestamp=data.get("timestamp", datetime.now().timestamp()),
            source=data.get("source", "agent"),
        )


@dataclass
class AgentMemory:
    """Memory storage for an agent."""

    agent_id: str
    entries: dict[str, AgentMemoryEntry] = field(default_factory=dict)

    def get(self, key: str) -> Any:
        """Get a value from memory."""
        entry = self.entries.get(key)
        return entry.value if entry else None

    def set(self, key: str, value: Any, source: str = "agent") -> None:
        """Set a value in memory."""
        self.entries[key] = AgentMemoryEntry(
            key=key,
            value=value,
            source=source,
        )

    def delete(self, key: str) -> bool:
        """Delete a key from memory."""
        if key in self.entries:
            del self.entries[key]
            return True
        return False

    def clear(self) -> None:
        """Clear all memory."""
        self.entries.clear()

    def keys(self) -> list[str]:
        """Get all keys."""
        return list(self.entries.keys())

    def to_dict(self) -> dict[str, Any]:
        """Serialize to dict."""
        return {
            "agent_id": self.agent_id,
            "entries": {k: v.to_dict() for k, v in self.entries.items()},
        }

    @staticmethod
    def from_dict(data: dict[str, Any]) -> AgentMemory:
        """Deserialize from dict."""
        memory = AgentMemory(agent_id=data["agent_id"])
        for key, entry_data in data.get("entries", {}).items():
            memory.entries[key] = AgentMemoryEntry.from_dict(entry_data)
        return memory


@dataclass
class AgentMemorySnapshot:
    """A snapshot of agent memory at a point in time."""

    agent_id: str
    timestamp: float
    memory: AgentMemory
    conversation_length: int = 0

    def to_dict(self) -> dict[str, Any]:
        return {
            "agent_id": self.agent_id,
            "timestamp": self.timestamp,
            "memory": self.memory.to_dict(),
            "conversation_length": self.conversation_length,
        }

    @staticmethod
    def from_dict(data: dict[str, Any]) -> AgentMemorySnapshot:
        return AgentMemorySnapshot(
            agent_id=data["agent_id"],
            timestamp=data["timestamp"],
            memory=AgentMemory.from_dict(data["memory"]),
            conversation_length=data.get("conversation_length", 0),
        )


class AgentMemoryManager:
    """Manages memory for multiple agents."""

    def __init__(self, storage_dir: str | None = None):
        self._memories: dict[str, AgentMemory] = {}
        self._snapshots: dict[str, list[AgentMemorySnapshot]] = {}
        self._storage_dir = storage_dir

    def get_memory(self, agent_id: str) -> AgentMemory:
        """Get or create memory for an agent."""
        if agent_id not in self._memories:
            self._memories[agent_id] = AgentMemory(agent_id=agent_id)
        return self._memories[agent_id]

    def delete_memory(self, agent_id: str) -> bool:
        """Delete memory for an agent."""
        if agent_id in self._memories:
            del self._memories[agent_id]
            return True
        return False

    def create_snapshot(
        self,
        agent_id: str,
        conversation_length: int = 0,
    ) -> AgentMemorySnapshot:
        """Create a snapshot of agent memory."""
        memory = self.get_memory(agent_id)
        snapshot = AgentMemorySnapshot(
            agent_id=agent_id,
            timestamp=datetime.now().timestamp(),
            memory=memory,
            conversation_length=conversation_length,
        )

        if agent_id not in self._snapshots:
            self._snapshots[agent_id] = []
        self._snapshots[agent_id].append(snapshot)

        return snapshot

    def get_snapshots(self, agent_id: str) -> list[AgentMemorySnapshot]:
        """Get all snapshots for an agent."""
        return self._snapshots.get(agent_id, [])

    def restore_from_snapshot(self, snapshot: AgentMemorySnapshot) -> None:
        """Restore memory from a snapshot."""
        self._memories[snapshot.agent_id] = snapshot.memory

    def save_to_disk(self, agent_id: str) -> bool:
        """Save agent memory to disk."""
        if not self._storage_dir:
            return False

        memory = self._memories.get(agent_id)
        if not memory:
            return False

        os.makedirs(self._storage_dir, exist_ok=True)
        path = os.path.join(self._storage_dir, f"{agent_id}.json")

        try:
            with open(path, "w") as f:
                json.dump(memory.to_dict(), f, indent=2)
            return True
        except (OSError, json.JSONDecodeError):
            return False

    def load_from_disk(self, agent_id: str) -> AgentMemory | None:
        """Load agent memory from disk."""
        if not self._storage_dir:
            return None

        path = os.path.join(self._storage_dir, f"{agent_id}.json")

        if not os.path.exists(path):
            return None

        try:
            with open(path) as f:
                data = json.load(f)
            memory = AgentMemory.from_dict(data)
            self._memories[agent_id] = memory
            return memory
        except (OSError, json.JSONDecodeError):
            return None


# Global memory manager instance
_memory_manager: AgentMemoryManager | None = None


def get_memory_manager() -> AgentMemoryManager:
    """Get the global memory manager."""
    global _memory_manager
    if _memory_manager is None:
        _memory_manager = AgentMemoryManager()
    return _memory_manager


def get_agent_memory(agent_id: str) -> AgentMemory:
    """Get memory for an agent."""
    return get_memory_manager().get_memory(agent_id)
