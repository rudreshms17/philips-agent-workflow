"""
A2A Agent Communicator
----------------------
Agent-to-Agent communication system with a shared message bus and shared memory.
"""

from datetime import datetime


class A2ACommunicator:
    def __init__(self):
        self.message_bus: list[dict] = []
        self.shared_memory: dict = {}

    def send_message(self, from_agent: str, to_agent: str, message_type: str, content: str) -> dict:
        """Append a message to the bus and return the message dict."""
        message = {
            "from_agent": from_agent,
            "to_agent": to_agent,
            "message_type": message_type,
            "content": content,
            "timestamp": datetime.utcnow().isoformat() + "Z",
        }
        self.message_bus.append(message)
        print(f"[A2A]: {from_agent} -> {to_agent}: {message_type}")
        return message

    def receive_messages(self, agent_name: str) -> list[dict]:
        """Return all messages where to_agent matches agent_name."""
        return [m for m in self.message_bus if m["to_agent"] == agent_name]

    def broadcast(self, from_agent: str, content: str) -> list[dict]:
        """Send a broadcast message to all agents (to_agent='ALL')."""
        return [self.send_message(from_agent, "ALL", "broadcast", content)]


# Singleton — all agents share the same bus
COMMUNICATOR = A2ACommunicator()
